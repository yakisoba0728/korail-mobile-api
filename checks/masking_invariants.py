"""마스킹 회귀 하네스.

두 방향을 **함께** 겁니다. v4 에서 한쪽만 보고 고치다가 과잉마스킹을
누출로 바꿔 먹었기 때문입니다(R4-D01).
  LEAK : 민감 값이 결과에 남으면 실패
  OVER : 비민감 토큰이 결과에서 사라지면 실패
"""
import sys, json

# 저장소 루트에서 실행하십시오: ``python3 checks/masking_invariants.py``
sys.path.insert(0, "src")
from korail_mobile_api.redaction import (
    redact_text, redact_url, redact_value, redact_payload, redact_mapping,
)
from korail_mobile_api.errors import KorailApiError

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


def _dup_kept(v):
    """중복 키가 **둘 다** 살아남았는지. 개수까지 셉니다."""
    out = redact_text(v)
    if out.count('"public"') < 2:
        return out + " <<DUP_DROPPED>>"
    return out


def _must_redact(v):
    """무언가는 반드시 가려져야 하는 사례. 아무 것도 안 가리면 실패."""
    out = redact_text(v)
    if "[REDACTED" not in out:
        return out + " <<NOTHING_REDACTED>>"
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
    for c, m in bad: print(f"  {c:16} {m}")
    return len(bad)

if __name__ == "__main__":
    sys.exit(1 if run() else 0)
