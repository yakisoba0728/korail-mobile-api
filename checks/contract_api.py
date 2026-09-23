"""합격 기준(``checks/ACCEPTANCE.md``)의 G8(표본)·G9·G10·G11 을 검사합니다.

수용 범위를 줄이지 않음, 파싱 실패 시 원문 보존, import 무결성, 로그아웃 뒤 로컬
상태 없음을 봅니다. G8 전체는 ``g8_differential.py`` 가 봅니다.

네트워크를 쓰지 않습니다. 만드는 클라이언트는 전부 ``httpx.MockTransport`` 를
달고, 그 전송이 실제로 불리면(= 가짜로 막지 않은 요청이 나가려 하면) 위반으로
기록합니다. 값은 전부 합성값입니다.

종료 코드: 0 통과, 1 실패, 2 검사 불완전 — 패키지 import 가 실패해 검사를 돌리지
못했거나, 검사기 자신이 예상하지 못한 예외로 멈춘 경우입니다. 불완전은 실패보다
우선합니다(``sphinx_symbols.py`` 와 같은 규칙): 끝까지 보지 못했으면 발견한 실패가
전부라고 말할 수 없습니다.

    python3 checks/contract_api.py
"""
from __future__ import annotations

import importlib
import pathlib
import pkgutil
import sys
import traceback
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

failures: list[str] = []
incomplete: list[str] = []


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


ENV = {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": "ok"}


def _offline_transport() -> Any:
    """불리면 위반을 기록하는 전송. 이 검사기는 네트워크에 닿으면 안 됩니다."""
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        check("NET", False, f"실제 전송 시도: {request.method} {request.url.path}")
        raise httpx.ConnectError("offline checker", request=request)

    return httpx.MockTransport(handler)


# --- G10: import 무결성 -----------------------------------------------------
def g10(pkg: Any) -> int:
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
    return len(modules)


# --- G8: 새 선택 필드가 파싱 실패를 만들지 않음 ---------------------------------
# 여기 있는 것은 **좁은 표본**입니다 — cart 일부 키, ticket 두 필드, cart-add 세
# 형태. 새로 모델링한 선택 필드군 전체를 필드마다 "예전 파서가 받던 응답을 새
# 파서도 받는가"로 비교하는 검사는 ``checks/g8_differential.py`` 가 합니다(최종
# 감사 C38). 이 파일의 G8 을 넓히지 말고 그쪽에 추가하십시오.
#: ``10**5000`` 은 파이썬의 정수→문자열 자릿수 한도(기본 4,300)를 넘어 ``str()`` 이
#: ``ValueError`` 를 냅니다. 관대화 코드가 그 예외를 놓쳤습니다(최종 감사 C10).
ODD = [True, 1.5, [], {}, None, 7, "s", 10**5000]
NEW_CART_KEYS = [
    "h_item_dv_cd", "h_add_srv_mrk_ent_id", "h_item_sqno", "h_jrny_sqno",
    "h_jrny_tp_cd", "utlClsDt", "h_stl_lmt_tm", "h_stl_extns_tno",
    "h_stl_mns_allw_val", "h_fld_stl_dv", "h_spvs_rs_stn_cd", "h_filler",
]


def g8() -> None:
    from korail_mobile_api import read_parsers as RP
    from korail_mobile_api.client import KorailClient
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.models import BaseKorailResponse
    from korail_mobile_api.mutation_parsers import parse_cart_add_response

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

    # 실제 파서가 ``_mutation`` 경로에서 자릿수 한도 초과 정수를 만나는 경우.
    # G8 사례입니다(파싱이 실패하면 안 됨) — 예전에는 G9 제목 아래 섞여 있었습니다.
    client = KorailClient(KorailConfig(), transport=_offline_transport())
    big = {**ENV, "psgDiscAdd_infos": {"psgDiscAdd_info": [{"h_psg_sqno": 10**5000}]}}
    with patch.object(
        client.http, "post_mutation_form",
        side_effect=lambda *_a, **_k: BaseKorailResponse.from_raw(big),
    ):
        try:
            client._mutation("cart", "/x", {}, parser=parse_cart_add_response)
        except Exception as error:  # noqa: BLE001
            check("G8", False, f"cart-add 큰 정수(_mutation): {type(error).__name__}")


# --- G9: 변경 응답의 typed 파싱 실패 시 .raw 에 원문 전체 ------------------------
#: 봉투만이 아닌 응답 — ``.raw`` 가 봉투 복사본이나 일부가 아니라 **받은 것
#: 전체**인지를 가릴 수 있게 본문 키를 둡니다.
FULL = {
    **ENV,
    "h_pnr_no": "SYNTHETIC-0001",
    "rows": {"row": [{"k": "a"}, {"k": "b"}]},
}
PARTIAL = {"partial": "only"}


def _partial_raw_errors() -> list[tuple[str, Callable[[], Exception]]]:
    """``raw`` 를 이미 채운 채 파서가 낼 수 있는 이 패키지의 예외들."""
    from korail_mobile_api import errors as E

    def with_raw(error: Exception) -> Exception:
        error.raw = dict(PARTIAL)  # type: ignore[attr-defined]
        return error

    return [
        ("KorailProtocolError", lambda: with_raw(E.KorailProtocolError("synthetic"))),
        ("KorailTransportError", lambda: with_raw(E.KorailTransportError("synthetic"))),
        ("KorailAuthError", lambda: with_raw(E.KorailAuthError("synthetic"))),
        ("KorailAppError", lambda: E.KorailAppError("E0000", "synthetic", raw=dict(PARTIAL))),
        ("KorailSoldOutError",
         lambda: E.KorailSoldOutError("ERR211161", "synthetic", raw=dict(PARTIAL))),
        ("KorailInvalidRequestError",
         lambda: E.KorailInvalidRequestError("E0001", "synthetic", raw=dict(PARTIAL))),
        ("KorailSessionExpiredError",
         lambda: E.KorailSessionExpiredError("P058", "synthetic", raw=dict(PARTIAL))),
        ("KorailDynaPathError", lambda: E.KorailDynaPathError("synthetic", raw=dict(PARTIAL))),
    ]


def g9() -> None:
    from korail_mobile_api.client import KorailClient
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.errors import KorailApiError, KorailProtocolError
    from korail_mobile_api.models import BaseKorailResponse

    client = KorailClient(KorailConfig(), transport=_offline_transport())

    def run(label: str, parser: Callable[[object], object]) -> BaseException | None:
        """``_mutation`` 을 한 번 돌리고 난 예외를 돌려줍니다. 전송은 정확히 1회여야."""
        calls = {"n": 0}

        def fake_post(*_args: object, **_kwargs: object) -> BaseKorailResponse:
            calls["n"] += 1
            return BaseKorailResponse.from_raw(
                {**FULL, "rows": {"row": [dict(r) for r in FULL["rows"]["row"]]}}
            )

        raised: BaseException | None = None
        with patch.object(client.http, "post_mutation_form", side_effect=fake_post):
            try:
                client._mutation("cart", "/x", {}, parser=parser)
                check("G9", False, f"{label}: 파싱 실패가 전파되지 않음")
            except Exception as error:  # noqa: BLE001
                raised = error
        check("G9", calls["n"] == 1, f"{label}: 전송 {calls['n']}회 (정확히 1회여야)")
        return raised

    # 1) raw 없는 KorailProtocolError
    def bad_parser(_raw: object) -> object:
        raise KorailProtocolError("typed parse failed")

    error = run("raw 없음", bad_parser)
    check("G9", isinstance(error, KorailProtocolError), f"raw 없음: {type(error).__name__}")
    check("G9", getattr(error, "raw", None) == FULL, f"raw 없음 .raw={show(getattr(error, 'raw', None))}")

    # 2) raw 를 **이미 일부로** 채운 예외들(최종 감사 C27/C39). ``.raw`` 는 받은 응답
    #    전체여야 하고, 파서가 넣었던 일부는 ``.parser_raw`` 에 남아야 합니다.
    for label, make in _partial_raw_errors():
        prototype = make()

        def partial_parser(_raw: object, _make: Callable[[], Exception] = make) -> object:
            raise _make()

        error = run(f"부분 raw {label}", partial_parser)
        check("G9", type(error) is type(prototype),
              f"부분 raw {label}: 예외 종류가 바뀜 → {type(error).__name__}")
        check("G9", isinstance(error, KorailApiError), f"부분 raw {label}: 패키지 예외 아님")
        check("G9", getattr(error, "raw", None) == FULL,
              f"부분 raw {label}: .raw={show(getattr(error, 'raw', None))} (전체여야)")
        check("G9", getattr(error, "parser_raw", None) == PARTIAL,
              f"부분 raw {label}: .parser_raw={show(getattr(error, 'parser_raw', None))}")

    # 3) 이 패키지의 예외가 아닌 것. ``except KorailApiError`` 만 있던 경계를 그대로
    #    빠져나가 ``.raw`` 가 없었습니다(최종 감사 C11).
    def foreign_parser(_raw: object) -> object:
        raise ValueError("synthetic non-package failure")

    error = run("외부 예외", foreign_parser)
    check("G9", isinstance(error, KorailProtocolError),
          f"외부 예외가 감싸지지 않음: {type(error).__name__}")
    check("G9", getattr(error, "raw", None) == FULL,
          f"외부 예외 .raw={show(getattr(error, 'raw', None))}")


# --- C26: logout 은 서버 요청이 어떻게 실패해도 로컬 상태를 비움 ------------------
def logout_state() -> None:
    import httpx

    from korail_mobile_api.client import KorailClient
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.errors import KorailTransportError
    from korail_mobile_api.models import KorailSession

    def logged_in(transport: Any) -> Any:
        client = KorailClient(KorailConfig(), transport=transport)
        client.session.current = KorailSession(
            jsessionid="SYNTHETIC-JSESSIONID", member_no="0000000000",
        )
        client.http.cookies.set(
            "JSESSIONID", "SYNTHETIC-JSESSIONID", domain="smart.letskorail.com"
        )
        return client

    def assert_cleared(label: str, client: Any, action: Callable[[], None]) -> None:
        try:
            action()
        except BaseException as error:  # noqa: BLE001
            check("C26", False, f"{label}: logout 이 {type(error).__name__} 를 냄")
        check("C26", client.session.current is None, f"{label}: current 가 남음")
        check("C26", client.session.pending is None, f"{label}: pending 이 남음")
        check("C26", len(client.http.cookies) == 0,
              f"{label}: 쿠키 {len(client.http.cookies)}개가 남음")

    # a) 전송 계층이 이 패키지 밖 예외를 냄
    for label, exc in (
        ("post_form RuntimeError", RuntimeError("synthetic closed client")),
        ("post_form KorailTransportError", KorailTransportError("synthetic")),
        ("post_form ValueError", ValueError("synthetic")),
    ):
        client = logged_in(_offline_transport())
        with patch.object(client.http, "post_form", side_effect=exc):
            assert_cleared(label, client, client.logout)

    # b) 실제 post_form 이 MockTransport 의 전송 오류를 만남
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic refuse", request=request)

    client = logged_in(httpx.MockTransport(refuse))
    assert_cleared("MockTransport ConnectError", client, client.logout)

    # c) 닫힌 HTTP 클라이언트 — httpx 가 전송 전에 RuntimeError 를 냅니다
    client = logged_in(_offline_transport())
    client.close()
    assert_cleared("닫힌 클라이언트", client, client.logout)


# ---------------------------------------------------------------------------
def main() -> int:
    try:
        import korail_mobile_api as pkg
    except Exception as error:  # noqa: BLE001
        print(f"검사 불완전 — 패키지 import 실패: {type(error).__name__}: {error}")
        return 2

    module_count = 0
    sections: list[tuple[str, Callable[[], object]]] = [
        ("G10", lambda: g10(pkg)),
        ("G8", g8),
        ("G9", g9),
        ("C26", logout_state),
    ]
    for name, section in sections:
        try:
            result = section()
            if name == "G10" and isinstance(result, int):
                module_count = result
        except ImportError as error:
            incomplete.append(f"{name}: import 실패 {type(error).__name__}: {error}")
        except Exception as error:  # noqa: BLE001
            # 검사 대상이 아니라 **검사기**가 예상하지 못한 곳에서 멈춘 것.
            # 끝까지 보지 못했으니 실패(1)가 아니라 불완전(2)입니다.
            where = traceback.extract_tb(error.__traceback__)[-1]
            incomplete.append(
                f"{name}: 검사기 예외 {type(error).__name__}: {show(str(error))}"
                f" ({pathlib.Path(where.filename).name}:{where.lineno})"
            )

    if failures:
        print(f"계약 위반 {len(failures)}건")
        for line in failures[:30]:
            print("  " + line)
    if incomplete:
        print(f"검사 불완전 {len(incomplete)}건")
        for line in incomplete:
            print("  " + line)
        return 2
    if failures:
        return 1
    print(f"G8·G9·G10·G11 통과 (모듈 {module_count}, 공개 심볼 {len(pkg.__all__)})")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException as error:  # noqa: BLE001
        if isinstance(error, SystemExit):
            raise
        print(f"검사 불완전 — 검사기 예외 {type(error).__name__}: {error}")
        code = 2
    sys.exit(code)
