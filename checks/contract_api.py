"""합격 기준(``checks/ACCEPTANCE.md``)의 G6·G8·G9·G10 을 검사합니다.

마스킹 사례 검사(G1~G7)는 ``masking_invariants.py`` 가 합니다. 이 스크립트는
나머지 계약 — 예외를 내지 않음, 수용 범위를 줄이지 않음, 파싱 실패 시 원문 보존,
import 무결성 — 을 봅니다.

종료 코드: 0 통과, 1 실패.

    python3 checks/contract_api.py
"""
import importlib
import pkgutil
import sys
from unittest.mock import patch

sys.path.insert(0, "src")

failures: list[str] = []


def show(value: object) -> str:
    """실패 메시지용 표시. 자릿수 한도를 넘는 정수의 ``repr`` 은 그 자체로
    ``ValueError`` 를 냅니다 — 검사기가 검사하려던 결함에 스스로 걸려 위반을
    보고하지 못하고 죽었습니다(2026-09-23)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return f"<int {value.bit_length()} bits>"
    try:
        return repr(value)[:40]
    except Exception:  # noqa: BLE001
        return f"<{type(value).__name__}>"


def check(cid: str, ok: bool, detail: str = "") -> None:
    if not ok:
        failures.append(f"{cid} {detail}")


# --- G10: import 무결성 -----------------------------------------------------
import korail_mobile_api as pkg  # noqa: E402

modules = [m.name for m in pkgutil.iter_modules(pkg.__path__)]
for name in modules:
    try:
        importlib.import_module(f"korail_mobile_api.{name}")
    except Exception as error:  # noqa: BLE001
        check("G10", False, f"import {name}: {type(error).__name__}")
undefined = [n for n in pkg.__all__ if not hasattr(pkg, n)]
check("G10", not undefined, f"__all__ 미정의: {undefined}")
namespace: dict[str, object] = {}
exec("from korail_mobile_api import *", namespace)  # noqa: S102
check("G10", all(n in namespace for n in pkg.__all__), "star import 누락")

# --- G6: 어떤 redact_* 도 str 입력에 예외를 내지 않음 ---------------------------
from korail_mobile_api import redaction as R  # noqa: E402

B = "\\"
NASTY = [
    "", " ", "﻿", "https://[invalid", "http://", "://", "?", "/?", "/?&=&",
    "[" * 20000 + "]" * 20000, "{" * 5000, '{"a":' * 3000, '"' * 1000,
    '{"x":NaN}', '{"x":1e999}', '{"x":"' + B + 'ud800"}', B + "u", B + "u00",
    "txtPwd=", "txtPwd=" + "&" * 100, "a" * 1_000_000, "\x00\x01\x7f",
    "h" + B + "u005fsgr=" + B + "u0022", 'INFO {"txtPwd":["]"', "JSESSIONID=",
    # 최종 감사: 쿼리의 짝 없는 surrogate(C08), scheme 생략 URL, 맨 숫자.
    "https://example.invalid/p?q=\ud800", "//user@host/p?q=\ud800",
    "//" + "a" * 5000 + "@h", "4111111111111111", "-", "1e999999",
]
#: G6 은 "어떤 ``redact_*`` 도 **str 입력에** 예외를 내지 않는다" 입니다. 예전에는
#: ``redact_payload``·``redact_mapping`` 에 문자열을 직접 넣지 않고 dict 값으로
#: 감싸서, 정작 명시된 조건을 검사하지 않았습니다(최종 감사 C09).
FUNCTIONS = (
    R.redact_text, R.redact_url, R.redact_value, R.redact_payload, R.redact_mapping,
)
for text in NASTY:
    for fn in FUNCTIONS:
        try:
            fn(text)
        except Exception as error:  # noqa: BLE001
            where = f"{fn.__name__}({show(text[:24])})"
            check("G6", False, f"{where}: {type(error).__name__}")
    try:
        R.redact_payload({"k": text, "l": [text]})
        R.redact_mapping({"k": text})
    except Exception as error:  # noqa: BLE001
        where = f"payload/mapping({show(text[:24])})"
        check("G6", False, f"{where}: {type(error).__name__}")

# --- G8: 새 선택 필드가 파싱 실패를 만들지 않음 ---------------------------------
from korail_mobile_api import read_parsers as RP  # noqa: E402
from korail_mobile_api.models import BaseKorailResponse  # noqa: E402
from korail_mobile_api.mutation_parsers import parse_cart_add_response  # noqa: E402

ENV = {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": "ok"}
#: ``10**5000`` 은 파이썬의 정수→문자열 자릿수 한도(기본 4,300)를 넘어 ``str()`` 이
#: ``ValueError`` 를 냅니다. 관대화 코드가 그 예외를 놓쳤습니다(최종 감사 C10).
ODD = [True, 1.5, [], {}, None, 7, "s", 10**5000]
NEW_CART_KEYS = [
    "h_item_dv_cd", "h_add_srv_mrk_ent_id", "h_item_sqno", "h_jrny_sqno",
    "h_jrny_tp_cd", "utlClsDt", "h_stl_lmt_tm", "h_stl_extns_tno",
    "h_stl_mns_allw_val", "h_fld_stl_dv", "h_spvs_rs_stn_cd", "h_filler",
]
for value in ODD:
    for key in NEW_CART_KEYS:
        try:
            RP.parse_cart_list_response(
                {**ENV, "cart_infos": {"cart_info": [{"h_pnr_no": "1", key: value}]}}
            )
        except Exception as error:  # noqa: BLE001
            check("G8", False, f"cart {key}={show(value)}: {type(error).__name__}")
    for key in ("ticketKind", "addSrvInfo"):
        try:
            RP.parse_ticket_list_response(
                BaseKorailResponse.from_raw(
                    {**ENV, "pnr_list": [{"h_pnr_no": "1", key: value}]}
                )
            )
        except Exception as error:  # noqa: BLE001
            check("G8", False, f"ticket {key}={show(value)}: {type(error).__name__}")
    for shape in (
        {"psgDiscAdd_infos": value},
        {"psgDiscAdd_infos": {"psgDiscAdd_info": value}},
        {"psgDiscAdd_infos": {"psgDiscAdd_info": [{"h_psg_sqno": value}]}},
    ):
        try:
            parse_cart_add_response({**ENV, **shape})
        except Exception as error:  # noqa: BLE001
            check("G8", False, f"cart-add {show(shape)}: {type(error).__name__}")

# --- G9: 변경 응답의 typed 파싱 실패 시 .raw 에 원문 ------------------------------
from korail_mobile_api.client import KorailClient  # noqa: E402
from korail_mobile_api.config import KorailConfig  # noqa: E402
from korail_mobile_api.errors import KorailProtocolError  # noqa: E402

client = KorailClient(KorailConfig())
calls = {"n": 0}


def _fake_post(*_args: object, **_kwargs: object) -> BaseKorailResponse:
    calls["n"] += 1
    return BaseKorailResponse.from_raw(dict(ENV))


def _bad_parser(_raw: object) -> object:
    raise KorailProtocolError("typed parse failed")


with patch.object(client.http, "post_mutation_form", side_effect=_fake_post):
    try:
        client._mutation("cart", "/x", {}, parser=_bad_parser)
        check("G9", False, "파싱 실패가 전파되지 않음")
    except KorailProtocolError as error:
        check("G9", getattr(error, "raw", None) == ENV, f".raw={show(error.raw)}")
check("G9", calls["n"] == 1, f"전송 {calls['n']}회 (재전송 금지)")


def _foreign_parser(_raw: object) -> object:
    # 이 패키지의 예외가 아닌 것. ``except KorailApiError`` 만 있던 경계를 그대로
    # 빠져나가 ``.raw`` 가 없었습니다(최종 감사 C11).
    raise ValueError("synthetic non-package failure")


with patch.object(client.http, "post_mutation_form", side_effect=_fake_post):
    try:
        client._mutation("cart", "/x", {}, parser=_foreign_parser)
        check("G9", False, "패키지 밖 예외가 전파되지 않음")
    except KorailProtocolError as error:
        check("G9", getattr(error, "raw", None) == ENV, f"외부 예외 .raw={show(error.raw)}")
    except Exception as error:  # noqa: BLE001
        check("G9", False, f"외부 예외가 감싸지지 않음: {type(error).__name__}")

    # 실제 파서가 자릿수 한도 초과 정수를 만나는 경우
    from korail_mobile_api.mutation_parsers import parse_cart_add_response as _pca
    big = {**ENV, "psgDiscAdd_infos": {"psgDiscAdd_info": [{"h_psg_sqno": 10**5000}]}}
    with patch.object(
        client.http, "post_mutation_form",
        side_effect=lambda *_a, **_k: BaseKorailResponse.from_raw(big),
    ):
        try:
            client._mutation("cart", "/x", {}, parser=_pca)
        except Exception as error:  # noqa: BLE001
            check("G8", False, f"cart-add 큰 정수: {type(error).__name__}")

# ---------------------------------------------------------------------------
if failures:
    print(f"계약 위반 {len(failures)}건")
    for line in failures[:30]:
        print("  " + line)
    sys.exit(1)
print(f"G6·G8·G9·G10 통과 (모듈 {len(modules)}, 공개 심볼 {len(pkg.__all__)},"
      f" G6 입력 {len(NASTY)}종)")
