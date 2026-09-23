"""마스킹 회귀 하네스.

두 방향을 **함께** 겁니다. v4 에서 한쪽만 보고 고치다가 과잉마스킹을
누출로 바꿔 먹었기 때문입니다(R4-D01).
  LEAK : 민감 값이 결과에 남으면 실패
  OVER : 비민감 토큰이 결과에서 사라지면 실패
"""
import sys, json

# 저장소 루트에서 실행하십시오: ``python3 checks/masking_invariants.py``
#
# 종료 코드: 0 통과, 1 사례 실패, 2 검사 불완전(대상 모듈을 import 조차 못 함).
# 변이 시험(``masking_mutants.py``)은 **1 만** "잡았다"로 셉니다. import 실패의
# traceback 도 종료 코드 1 이라, 문법이 깨진 변이가 "잡힌" 것으로 셈해졌습니다.
sys.path.insert(0, "src")
try:
    from korail_mobile_api.redaction import (
        redact_text, redact_url, redact_value, redact_payload, redact_mapping,
    )
    from korail_mobile_api.errors import KorailApiError
except Exception as _import_error:  # noqa: BLE001
    print(f"검사 불완전: 마스킹 모듈 import 실패 — {type(_import_error).__name__}: {_import_error}")
    sys.exit(2)

SEC = "PRIVATE_SENTINEL"; TAIL = "PRIVATE_TAIL"; PUB = "PUBLIC_MARKER"

# (id, 입력, 적용함수, 남으면 안 되는 것들, 사라지면 안 되는 것들)
def _json_ok(v):
    """마스킹 결과가 여전히 파싱 가능한 JSON 인지. 아니면 표식을 남겨 실패시킵니다."""
    import json as _j
    out = redact_text(v)
    try:
        _j.loads(out)
    except Exception:
        return out + " <<BROKEN_JSON>>"
    return out


def _two_entries(v):
    """숫자 키를 가려서 항목이 합쳐지지 않는지."""
    import json as _j
    out = redact_text(v)
    try:
        if len(_j.loads(out)) < 2:
            return out + " <<MERGED_ENTRIES>>"
    except Exception:
        return out + " <<BROKEN_JSON>>"
    return out


def _pairs(text):
    """JSON 을 **순서 있는 (키, 값) 목록**으로. dict 로 받으면 중복이 사라집니다."""
    return json.loads(text, object_pairs_hook=lambda items: items)


def _dup_kept(v):
    """중복 키의 순서 있는 (키, 값) 대응이 **그대로**인지.

    예전에는 키 문자열의 출현 횟수와 값 문자열의 존재만 봐서, 두 값이 모두
    ``SECOND`` 가 되고 ``FIRST`` 는 다른 키로 옮겨 간 출력도 통과했습니다
    (2026-09-23 확인). 이제 원래 쌍 목록과 통째로 비교합니다.
    """
    out = redact_text(v)
    try:
        if _pairs(out) != _pairs(v):
            return out + " <<PAIRS_CHANGED>>"
    except ValueError:
        return out + " <<BROKEN_JSON>>"
    return out


def _must_redact(v):
    """무언가는 반드시 가려져야 하는 사례. 아무 것도 안 가리면 실패."""
    out = redact_text(v)
    if "[REDACTED" not in out:
        return out + " <<NOTHING_REDACTED>>"
    return out


def _dup_kept_masked(v):
    """민감 필드가 **섞인** 중복 키 문서에서, 비민감 쌍이 순서째 그대로인지.

    민감 필드가 없는 문서는 "가린 게 없으면 원문 반환" 규칙 때문에 순회를 아예
    타지 않습니다. 그래서 중복 키를 버리는 순회 결함을 그 사례로는 못 잡았고,
    변이 시험이 그것을 드러냈습니다(2026-09-23).
    """
    out = redact_text(v)
    try:
        def public(pairs):
            return [(k, x) for k, x in pairs if k != "txtPwd"]
        if public(_pairs(out)) != public(_pairs(v)):
            return out + " <<PAIRS_CHANGED>>"
    except ValueError:
        return out + " <<BROKEN_JSON>>"
    return out


def _deep_mapping(_tag):
    """민감 키를 dict 1,500겹으로 감쌉니다. 재귀판은 여기서 죽었습니다(C02)."""
    node = {"txtPwd": SEC}
    for _ in range(1500):
        node = {"x": node}
    return str(redact_mapping(node))


# --- 외부 감사 C01~C10·C37 용 판정 함수 -------------------------------------
CARD = "4111111111111111"
#: 깊은 사례의 겹 수. 감사(Python 3.13)는 1만 겹에서 ``json.loads`` 와 ``str()`` 이
#: ``RecursionError`` 를 냈지만, 3.14 는 C 스택 기준이라 1만 겹은 통과하고 각각
#: 약 20만·10만 겹에서 실패합니다(2026-09-23, macOS 3.14.7 확인). 1만 겹으로 두면
#: 3.14 에서는 옛 구현도 통과해 사례가 아무 것도 못 잡습니다. 두 버전 모두에서
#: 표준 구현이 실패하는 깊이로 둡니다.
DEPTH = 300_000


def _numbers_kept(v):
    """카드번호 모양이 아닌 숫자 리터럴이 **한 글자도** 안 바뀌는지(C37).

    ``1e0`` 이 ``1.0`` 으로, ``-0.10`` 이 ``-0.1`` 로 바뀌어도 값은 같아서, 값만
    비교하는 사례로는 숫자를 정규화하는 구현을 못 잡았습니다.
    """
    out = redact_text(v)
    try:
        def literals(text):
            return [
                (k, x) for k, x in json.loads(
                    text,
                    object_pairs_hook=lambda items: items,
                    parse_float=lambda s: ("NUM", s),
                    parse_int=lambda s: ("NUM", s),
                )
                if isinstance(x, tuple)
            ]
        if literals(out) != literals(v):
            return out + " <<NUMBER_CHANGED>>"
    except ValueError:
        return out + " <<BROKEN_JSON>>"
    return out


def _entries_kept(fn):
    """가린 키끼리, 또는 가린 키와 원래 키가 **겹쳐 항목이 사라지지 않는지**(C06)."""
    def check(v):
        out = fn(v)
        if isinstance(out, str):
            try:
                pairs = _pairs(out)
            except ValueError:
                return out + " <<BROKEN_JSON>>"
            keys = [k for k, _ in pairs]
            values = sorted(x for _, x in pairs)
        else:
            keys = list(out)
            values = sorted(out.values())
        if len(set(keys)) != len(keys) or len(keys) != len(v):
            return f"{out} <<KEYS_COLLIDED>>"
        if values != sorted(v.values()):
            return f"{out} <<VALUES_LOST>>"
        return str(out)
    return check


def _entries_json(v):
    """JSON 판 :func:`_entries_kept`. 없던 중복 키가 생기면 실패입니다."""
    out = redact_text(v)
    try:
        pairs = _pairs(out)
    except ValueError:
        return out + " <<BROKEN_JSON>>"
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys) or len(keys) != len(_pairs(v)):
        return out + " <<KEYS_COLLIDED>>"
    if sorted(x for _, x in pairs) != sorted(x for _, x in _pairs(v)):
        return out + " <<VALUES_LOST>>"
    return out


def _shared_kept(_tag):
    """순환하지 않는 공유 객체는 나올 때마다 **다 가려서** 써야 합니다(C07)."""
    shared = {"public": PUB, "txtPwd": SEC}
    out = redact_mapping({"left": shared, "right": shared, "list": [shared]})
    want = {"public": PUB, "txtPwd": "[REDACTED]"}
    if out["left"] != want or out["right"] != want or out["list"] != [want]:
        return f"{out} <<SHARED_LOST>>"
    return str(out)


def _cycle_marked(_tag):
    """진짜 순환은 여전히 ``[CYCLE]`` 이고, 멈춰야 합니다."""
    node = {"public": PUB, "txtPwd": SEC}
    node["self"] = node
    node["via"] = [node]
    out = redact_mapping(node)
    if out["self"] != "[CYCLE]" or out["via"] != ["[CYCLE]"]:
        return f"{out} <<CYCLE_NOT_MARKED>>"
    return str(out)


def _deep_payload(_tag):
    """폼 값 :data:`DEPTH` 겹. 가린 **뒤** 의 문자열화까지 재귀가 없어야 합니다(C08)."""
    node = {"txtPwd": SEC}
    for _ in range(DEPTH):
        node = {"child": node}
    out = redact_payload(node)["child"]
    if "'txtPwd': '[REDACTED]'" not in out:
        return out[-80:] + " <<NOT_REDACTED>>"
    return out[-80:]


_DEEP_DOC = (
    '{"public":' * DEPTH
    + '{"txtPwd":{"a":{"b":1},"tail":"%s"}}' % SEC
    + "}" * DEPTH
)


def _deep_json(_tag):
    """표준 ``json.loads`` 가 거절하는 :data:`DEPTH` 겹 JSON 도 **구조로** 가려야 합니다.

    예전(옛 한계 L6)에는 자유 텍스트 경로로 가서 안쪽 괄호에서 끊겨 비밀이 남았고,
    따옴표 없는 ``[REDACTED]`` 가 들어가 JSON 이 아니었습니다. 기대 출력을 글자
    그대로 비교합니다 — 이 깊이는 표준 json 으로 다시 읽어 확인할 수 없습니다.
    """
    out = redact_text(_DEEP_DOC)
    want = (
        '{"public": ' * DEPTH + '{"txtPwd": "[REDACTED]"}' + "}" * DEPTH
    )
    if out != want:
        return out[DEPTH * 10 : DEPTH * 10 + 120] + " <<NOT_STRUCTURAL>>"
    return out[-60:]


def _deep_prose(_tag):
    """산문 뒤의 :data:`DEPTH` 겹 JSON. 비밀도, 따옴표 없는 ``[REDACTED]`` 도 없어야 합니다."""
    out = redact_text("INFO " + _DEEP_DOC)
    want = (
        "INFO " + '{"public":' * DEPTH + '{"txtPwd":"[REDACTED]"}' + "}" * DEPTH
    )
    if out != want:
        return out[DEPTH * 10 : DEPTH * 10 + 120] + " <<PROSE_DEEP_WRONG>>"
    return out[-60:]


def _prose_json_ok(v):
    """``INFO `` 뒤에 박힌 JSON 조각이 가린 뒤에도 JSON 인지(따옴표 없는 치환 금지)."""
    out = redact_text(v)
    head, _, body = out.partition(" ")
    try:
        json.loads(body)
    except ValueError:
        return out + " <<BROKEN_EMBEDDED_JSON>>"
    return out


CASES = [
 # --- v3 에서 이미 맞던 것 (회귀 방지)
 ("base/text",     f"h_sgr_nm={SEC}",                     redact_text, [SEC], []),
 ("base/index",    f"h_sgr_nm_1={SEC}",                   redact_text, [SEC], []),
 ("base/json",     '{"h_sgr_nm_1":"%s"}' % SEC,           redact_text, [SEC], []),
 ("base/absurl",   f"https://a.b/p?h_sgr_nm_1={SEC}",     redact_url,  [SEC], []),
 ("base/relurl",   f"/p?h_sgr_nm_1={SEC}",                redact_url,  [SEC], []),
 ("base/neigh",    f"/p?h_sgr_nm_1={SEC}&trnNo1={PUB}",   redact_url,  [SEC], [PUB]),
 # --- R4-D01 내가 만든 회귀: 구분자가 값 **안**에 있을 때
 ("D01/cookie;",   f"Cookie: audit=HEAD;other={TAIL}",    redact_text, [TAIL], []),
 ("D01/pwd&",      f"txtPwd=HEAD&{TAIL}",                 redact_text, [TAIL], []),
 ("D01/name;",     f"h_sgr_nm=HEAD;{TAIL}",               redact_text, [TAIL], []),
 # --- R3-D02 이웃 보존 (평문에서도)
 ("D02/neightext", f"txtSeatNo1_={SEC}&trnNo1={PUB}",     redact_text, [SEC], [PUB]),
 ("D02/jsess",     f"h_sgr_nm={SEC};jsessionid=abc",      redact_text, [SEC], []),
 # --- R4-D05 빈 값이 다음 필드를 삼키면 안 됨
 # 2026-09-23: 의도적으로 과잉 마스킹을 택했습니다. gap 가드를 두면
 # ``txtPwd= <base64>`` 가 새므로, 공백 뒤 토큰은 값으로 봅니다. 이웃이
 # 함께 가려지는 것은 진단 손실이지 누출이 아닙니다.
 ("D05/empty",     f"h_sgr_nm_1= trnNo1={PUB}",           _must_redact, [], []),
 # --- R4-D02 percent-encoded 키
 ("D02/pct_text",  f"h%5Fsgr%5Fnm_1={SEC}",               redact_text, [SEC], []),
 ("D02/pct_get",   f"GET /x?h%5Fsgr%5Fnm_1={SEC}",        redact_value,[SEC], []),
 ("D02/pct_pay",   {"note": f"/x?h%5Fsgr%5Fnm_1={SEC}"},  redact_payload,[SEC], []),
 # --- R4-D03 JSON escape 키
 ("D03/escaped",   '{"h\\u005fsgr\\u005fnm_1":"%s"}'%SEC, redact_text, [SEC], []),
 # --- R4-D04 직렬화된 배열/객체
 ("D04/jsonarr",   '{"hidDscpNo": ["HEAD", "%s"]}' % TAIL,redact_text, [TAIL], []),
 ("D04/pyrepr",    "{'hidDscpNo': ['HEAD', '%s']}" % TAIL,redact_text, [TAIL], []),
 ("D04/nested",    '{"a":{"h_sgr_nm":"%s"},"b":"%s"}'%(SEC,PUB), redact_text,[SEC],[PUB]),
 # --- 구조화 경로는 계속 맞아야 함
 ("struct/map",    {"h_sgr_nm_1": SEC, "trnNo1": PUB},    redact_mapping,[SEC],[PUB]),
 ("struct/list",   {"hidDscpNo": [SEC, TAIL], "t": PUB},  redact_payload,[SEC,TAIL],[PUB]),
 # --- 비민감 대조군: 절대 지워지면 안 됨
 ("ctl/hour",      f"txtGoHour={PUB}",                    redact_text, [], [PUB]),
 ("ctl/trn",       f"trnNo1={PUB}",                       redact_text, [], [PUB]),
 ("ctl/psg",       f"psgNum1_={PUB}",                     redact_text, [], [PUB]),
 ("ctl/lang",      f"lang={PUB}",                         redact_text, [], [PUB]),
 ("ctl/sentence",  f"오류? a={PUB} 입니다",                redact_value,[], [PUB]),
 ("ctl/plainpath", "/classes/com.korail.mobile.Login.do", redact_value,[], ["Login.do"]),
 ("ctl/msg",       f"WRR664260: 예약 존재 {PUB}",          redact_text, [], [PUB,"WRR664260"]),
 # --- 예외 경로
 ("exc/str",       f"failed h_sgr_nm_1={SEC}&trnNo1={PUB}", lambda s: str(KorailApiError(s)), [SEC],[PUB]),
 # --- 파싱 불가 입력에서 예외 금지
 ("robust/badurl", "https://[invalid",                    redact_value,[], []),
 # --- v7 회귀: JSON **안의** 로그 문자열. 이 사례가 없어서, 그 수정을
 # 되돌린 변이가 하네스를 그대로 통과했습니다(2026-09-23 확인).
 ("v7/json_inner",  '{"detail":"txtPwd=%s"}' % SEC,
                    redact_text, [SEC], ["detail"]),
 ("v7/json_inner2", '["txtPwd=%s"]' % SEC,                 redact_text, [SEC], []),
 ("v7/json_inner3", '{"a":{"b":"Cookie: a=%s"}}' % SEC, redact_text, [SEC], []),
 # --- v8 회귀: 로그 전체의 escape 를 먼저 풀면 값 안의 \u0022 가 따옴표가 됨
 ("v8/esc_quote",   'INFO {"txtPwd":"HEAD\\u0022%s"}' % SEC, redact_text, [SEC], []),
 # --- v8 회귀: 공개 값의 리터럴 escape 는 그대로여야 함
 ("v8/esc_literal", '{"detail":"\\\\u0061"}',            redact_text, [], ["u0061"]),
 ("v8/esc_path",    "file C:\\u0041\\u0042\\report.txt",
                    redact_text, [], ["u0041", "u0042"]),
 # --- 접두 산문 + escape 된 키 (키 쪽 패턴이 받아야 함)
 # --- v8: 접두 산문 + 배열/객체 안 문자열의 ``]``·``}``
 # --- 인덱스 접미사 앞 밑줄까지 escape 된 키 (전 레지스트리 시험에서 1,571건)
 ("v8/esc_suffix",
  'INFO {"h\\u005fsgr\\u005fnm\\u005f1":"%s"}' % SEC,
  redact_text, [SEC], []),
 # --- 최종 감사 C01~C09. 구조화 입력은 깊이·타입과 무관하게(G1).
 # C12: 이 묶음이 없어서 "최상위 한 겹만 가리는" 구현이 하네스를 통과했습니다.
 ("final/dup_masked",
  '{"public":"FIRST","public":"SECOND","txtPwd":"%s"}' % SEC,
  _dup_kept_masked, [SEC], ["FIRST", "SECOND"]),
 ("final/nested_map",   {"outer": {"txtPwd": SEC}},
                         redact_mapping, [SEC], ["outer"]),
 ("final/nested_list",  {"a": [{"b": {"txtPwd": SEC}}]},    redact_value,   [SEC], []),
 ("final/C01_payload",  {"outer": {"txtPwd": [["a", SEC]]}},
                         redact_payload, [SEC], []),
 ("final/C02_deep",     "deep1500",                          _deep_mapping,  [SEC], []),
 ("final/C03_schemerel", "//%s@example.invalid/p" % SEC,     redact_url,     [SEC],
                         ["example.invalid"]),
 ("final/C04_barecard", "4111111111111111",                  _json_ok,
                         ["4111111111111111"], []),
 ("final/C05_strval",   '{"detail":"[1,2]"}',
                         redact_text, [], ['"[1,2]"']),
 ("final/C06_quotelf",  'txtPwd="HEAD\\\n%s"' % SEC,         redact_text, [SEC], []),
 ("final/C07_host",     "https://4111111111111111.example.invalid/p",
                         redact_url, ["4111111111111111"], ["example.invalid"]),
 ("final/C08_surrogate", "https://example.invalid/p?q=\ud800",
                         redact_url, [], ["example.invalid"]),
 ("final/C09_payloadstr", "plain txtPwd=%s" % SEC,             redact_payload, [SEC],
                         ["plain"]),
 ("final/G5_cardkey",   '{"4111111111111111":"A","5555555555554444":"B"}',
                         _two_entries, ["4111111111111111", "5555555555554444"], []),
 ("v8/prefix_arr",  'INFO {"txtPwd":["]","%s"]}' % SEC,     redact_text, [SEC], []),
 ("v8/prefix_obj",  'INFO {"txtPwd":{"a":"}","b":"%s"}}' % SEC, redact_text, [SEC], []),
 ("v8/esc_key",     'INFO {"h\\u005fsgr\\u005fnm_1":"%s"}' % SEC,
                    redact_text, [SEC], []),
 # --- v5 회귀: '=' 를 품은 값 (base64 패딩 포함)
 ("v5/base64pad2",  "txtPwd=U0VDUkVUQQ==",                 redact_text, ["U0VDUkVUQQ"], []),
 ("v5/base64pad1",  "txtPwd=U0VDUkVUQUI=",                 redact_text, ["U0VDUkVUQUI"], []),
 ("v5/eq_in_value", f"txtPwd={SEC}={TAIL}",                redact_text, [SEC, TAIL], []),
 # --- v5: 값이 구분자로 시작하고 뒤에 새 키가 없으면 값의 일부
 ("v5/lead_amp",    f"txtPwd=&{SEC}",                      redact_text, [SEC], []),
 ("v5/lead_semi",   f"txtPwd=;{SEC}",                      redact_text, [SEC], []),
 # --- v5: JSON 숫자형 카드번호가 CARD_RE 를 건너뛰면 안 됨
 ("v5/json_card",   '{"debug":4111111111111111}',          redact_text, ["4111111111111111"], []),
 ("v5/arr_card",    '[4111111111111111]',                  redact_text, ["4111111111111111"], []),
 # --- v5: CRLF 가 다음 줄을 먹으면 안 됨
 ("v5/crlf",        f"txtPwd=\r\nINFO {PUB}",              redact_text, [], ["INFO", PUB]),
 # --- v5: userinfo 누출 세 형태 + 과잉 마스킹 한 형태
 ("v5/ui_useronly", f"https://{SEC}@example.invalid",      redact_text, [SEC], []),
 ("v5/ui_emptyuser",f"https://:{SEC}@example.invalid",     redact_text, [SEC], []),
 ("v5/ui_multi_at", f"https://user:pass@{SEC}@example.invalid:8443/p", redact_text, [SEC], ["example.invalid"]),
 ("v5/sessboundary",f"notJSESSIONID={PUB}",             redact_text, [], [PUB]),
 ("v5/sess_real",   "JSESSIONID=PRIVATE_SENTINEL",        redact_text, [SEC], []),
 ("v5/hyphen_key",  f"set-cookie={SEC}",                  redact_text, [SEC], []),
 ("v5/hyphen_pct",  f"set%2Dcookie={SEC}",                redact_text, [SEC], []),
 # 예전에는 ``FIRST`` 보존만 봤습니다. 둘째 값을 지운 구현도 통과했습니다.
 ("v5/json_dupkey", '{"public":"FIRST","public":"SECOND"}',
                    _dup_kept, [], ["FIRST", "SECOND"]),
 ("v5/json_surrog", '{"public":"\\ud800"}',               lambda v: redact_text(v).encode("utf-8").decode("utf-8"), [], []),
 # --- v6: 손실 감지로 비켜가도 escape 된 민감 키는 가려져야 함
 ("v6/bail_escaped", '{"x":1,"x":2,"h\\u005fsgr\\u005fnm_1":"%s"}' % SEC, redact_text, [SEC], []),
 ("v6/bail_float",   '{"public":1e0,"h\\u005fsgr\\u005fnm_1":"%s"}' % SEC, redact_text, [SEC], []),
 ("v6/bail_array",   '{"x":1,"x":2,"hidDscpNo":["]","%s"]}' % SEC,   redact_text, [SEC], []),
 # --- v6: JSON 출력이 유효한 JSON 이어야 함
 ("v6/json_valid1",  '{"debug":4111111111111111}',           _json_ok, ["<<"], []),
 ("v6/json_valid2",  '[4111111111111111]',                   _json_ok, ["<<"], []),
 ("v6/json_valid3",  '{"debug":"JSESSIONID=%s"}' % SEC,      _json_ok, [SEC], []),
 # --- v6: 출력에 중복 키를 만들면 안 됨 (항목이 합쳐짐)
 ("v6/no_dupkey",    '{"4111111111111111":"A","5555555555554444":"B"}', _two_entries, ["<<"], []),
 # --- v6: 공백 뒤 base64/등호 값
 ("v6/gap_b64",      "txtPwd= U0VDUkVUX0JBU0U2NA==",         redact_text, ["U0VDUkVU"], []),
 ("v6/gap_equals",   f"txtPwd=    {SEC}={TAIL}",             redact_text, [SEC, TAIL], []),
 ("v5/ui_notauth",  "https://example.invalid:443?contact=user@example.net", redact_text, [], ["example.invalid", "contact"]),
 # --- R4-A02 / 로 시작하는 문장이 쿼리로 해석돼 공백이 + 로 바뀌면 안 됨
 ("A02/slashprose", f"/로그? a=b {PUB}",                    redact_value,[], [PUB, "a=b"]),
 ("A02/realurl",    f"/x.do?h_sgr_nm_1={SEC}&trnNo1={PUB}", redact_value,[SEC],[PUB]),
 # --- v4 진입점 행렬에 남아 있던 잔존 누출
 ("M/userinfo",    f"https://audit:{SEC}@example.invalid/x?lang=ko", redact_url, [SEC], ["example.invalid"]),
 ("M/userinfo_txt",f"https://audit:{SEC}@example.invalid/x?lang=ko", redact_text,[SEC], []),
 ("M/json_str",    '"{\\"h_sgr_nm_1\\": \\"%s\\"}"' % SEC,   redact_text, [SEC], []),
 ("M/empty_amp",   f"h_sgr_nm_1=&trnNo1={PUB}",           redact_text, [], [PUB]),
 ("M/empty_semi",  f"h_sgr_nm_1=;trnNo1={PUB}",           redact_text, [], [PUB]),
 ("M/bs_json",     '{\\"h_sgr_nm_1\\":\\"%s\\"}' % SEC,      redact_text, [SEC], []),
 # --- 외부 감사 C01~C10·C37. 두 방향 모두: 새지 않고, 계약이 남기라는 이웃은 남긴다.
 # C01: 폼 키의 카드번호
 ("C01/pay_cardkey",   {CARD: PUB},                          redact_payload, [CARD], [PUB]),
 ("C01/pay_keepkey",   {"lang": PUB, CARD: "x"},             redact_payload, [CARD], ["'lang'", PUB]),
 # C02: 쿼리 키의 카드번호
 ("C02/url_cardkey",   f"https://example.invalid/?{CARD}={PUB}&lang=ko",
                        redact_url, [CARD], [PUB, "lang=ko", "example.invalid"]),
 ("C02/relurl_cardkey", f"/p?{CARD}={PUB}",                  redact_url, [CARD], [PUB]),
 # C03: 키·host 의 JSESSIONID= 값
 ("C03/json_sesskey",  json.dumps({f"JSESSIONID={SEC}": PUB}), _json_ok, [SEC], [PUB, "JSESSIONID="]),
 ("C03/map_sesskey",   {f"JSESSIONID={SEC}": PUB},           redact_mapping, [SEC], [PUB]),
 ("C03/pay_sesskey",   {f"JSESSIONID={SEC}": PUB},           redact_payload, [SEC], [PUB]),
 ("C03/url_host",      f"https://JSESSIONID={SEC}.example.invalid/?lang={PUB}",
                        redact_url, [SEC], [PUB]),
 # C04: 부호·소수·지수가 붙은 JSON 숫자의 카드번호. 출력은 여전히 JSON.
 ("C04/neg",           '{"n":-%s,"p":"%s"}' % (CARD, PUB),   _json_ok, [CARD], [PUB]),
 ("C04/decimal",       '{"n":%s.5}' % CARD,                  _json_ok, [CARD], []),
 ("C04/exponent",      '[%se5, 1.%sE-3]' % (CARD, CARD),     _json_ok, [CARD], []),
 # C37: 카드번호 모양이 아닌 숫자는 글자 그대로
 ("C37/numbers",       '{"n":1e0,"m":-0.10,"big":12345678901234567890,"txtPwd":"%s"}' % SEC,
                        _numbers_kept, [SEC], ["1e0", "-0.10", "12345678901234567890"]),
 # C05: 쉼표는 따옴표 없는 값을 끝내지 않음. G7 이웃은 그대로.
 ("C05/comma",         f"txtPwd=HEAD,{SEC}",                 redact_text, [SEC], []),
 ("C05/comma_colon",   f"txtPwd: HEAD,{SEC} next",           redact_text, [SEC], ["next"]),
 ("C05/comma_neigh",   f"txtGoHour={PUB}&txtPwd=HEAD,{SEC}&trnNo1={PUB}1;lang={PUB}2&psgNum1_={PUB}3",
                        redact_text, [SEC], [f"txtGoHour={PUB}", f"trnNo1={PUB}1", f"lang={PUB}2", f"psgNum1_={PUB}3"]),
 # C06: 가린 키가 원래 키와 겹쳐 항목이 사라지거나 중복 키가 생기면 안 됨
 ("C06/map_collision", {CARD: "A", "[REDACTED_CARD]": "B"},  _entries_kept(redact_mapping), [CARD], []),
 ("C06/pay_collision", {CARD: "A", "[REDACTED_CARD]": "B"},  _entries_kept(redact_payload), [CARD], []),
 ("C06/json_collision", json.dumps({CARD: "A", "[REDACTED_CARD]": "B", "[REDACTED_CARD]#2": "C"}),
                        _entries_json, [CARD], []),
 # C07: 공유 객체는 순환이 아님. 진짜 순환은 [CYCLE].
 ("C07/shared",        "shared",                             _shared_kept, [SEC], [PUB]),
 ("C07/cycle",         "cycle",                              _cycle_marked, [SEC], [PUB, "[CYCLE]"]),
 # C08: 깊은 폼 값(:data:`DEPTH` 겹)
 ("C08/pay_deep",      "deep",                               _deep_payload, [SEC], []),
 # C09: 구조 경로 실패(짝 없는 surrogate) 후에도 퍼센트 인코딩 키의 값은 가림
 ("C09/fallback_pct",  f"https://example.invalid/?%74xtPwd={SEC}&q=\ud800&lang={PUB}",
                        redact_url, [SEC], [PUB, "example.invalid"]),
 ("C09/fallback_plain", f"https://example.invalid/p?txt%50wd={SEC}&q=\ud800#f",
                        redact_url, [SEC], ["example.invalid", "#f"]),
 # C10: 괄호 값은 깊이와 무관하게 짝이 맞는 곳까지. 뒤 이웃은 그대로.
 ("C10/prose_nested",  'INFO {"txtPwd":{"a":{"b":1},"other":"%s"},"pub":"%s"}' % (SEC, PUB),
                        _prose_json_ok, [SEC], [PUB]),
 ("C10/prose_arr",     'INFO {"hidDscpNo":[["a"],["]","%s"]],"pub":"%s"}' % (SEC, PUB),
                        _prose_json_ok, [SEC], [PUB]),
 ("C10/eq_nested",     'txtPwd={"a":{"b":1},"c":"%s"}&trnNo1=%s' % (SEC, PUB),
                        redact_text, [SEC], [f"trnNo1={PUB}"]),
 ("C10/unbalanced",    'INFO {"txtPwd":{"a":"%s' % SEC,       redact_text, [SEC], []),
 ("C10/after_bracket", f"txtPwd=[a]{SEC}",                   redact_text, [SEC], []),
 # 옛 한계 L6: json.loads 가 거절하는 깊이도 구조로
 ("C10/deep_json",     "deep",                               _deep_json, [SEC], []),
 ("C10/deep_prose",    "deep",                               _deep_prose, [SEC], []),
]

#: :func:`_json_ok`·:func:`_two_entries` 가 붙이는 결함 표식. 사례마다 금지
#: 목록에 손으로 넣게 했더니 **빠뜨린 사례가 생겼고**, 깨진 JSON 을 돌려주는
#: 구현이 그대로 통과했습니다(2026-09-23 확인). 이제 모든 사례에 강제합니다.
DEFECT_MARK = "<<"


def run():
    bad = []
    for cid, inp, fn, leaks, keeps in CASES:
        leaks = list(leaks) + [DEFECT_MARK]
        try:
            out = str(fn(inp))
        except Exception as e:
            bad.append((cid, f"RAISED {type(e).__name__}: {e}")); continue
        for s in leaks:
            if s in out: bad.append((cid, f"LEAK {s!r} -> {out[:70]}"))
        for s in keeps:
            if s not in out: bad.append((cid, f"OVER lost {s!r} -> {out[:70]}"))
    print(f"cases: {len(CASES)}  failures: {len(bad)}")
    # 출력에 짝 없는 surrogate 가 섞일 수 있습니다(C09 사례). 그대로 찍으면
    # 보고하려던 실패가 UnicodeEncodeError 로 바뀝니다.
    for c, m in bad:
        print(f"  {c:16} {m}".encode("utf-8", "backslashreplace").decode("utf-8"))
    return len(bad)

if __name__ == "__main__":
    # 사례 안의 예외는 run() 이 실패로 셉니다. 여기까지 올라온 예외는 하네스
    # 자체의 고장이므로 "사례 실패(1)"가 아니라 "검사 불완전(2)"입니다.
    try:
        failed = run()
    except Exception as error:  # noqa: BLE001
        print(f"검사 불완전: 하네스 오류 — {type(error).__name__}: {error}")
        sys.exit(2)
    sys.exit(1 if failed else 0)
