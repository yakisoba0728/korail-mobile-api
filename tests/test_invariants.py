# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""손으로 유지하는 표와 목록이 서로 어긋나지 않는지 확인합니다.

``ebc4d5f`` 가 ``tests/`` 121파일 33,071줄을 지우면서, 커밋 메시지에 무엇이
남는지를 직접 적어 두었습니다 — "the route table counts, the ``__all__`` public
surface, parser regressions, the redaction sweep, ``verify_distribution.py``'s own
behaviour, and the docs index."

이 파일은 그 목록 가운데 **라이브러리가 스스로 확인할 수 있는 것**을 덮습니다.
파서 회귀는 골든 픽스처가 있어야 해서 마지막까지 비어 있었고, 이제
``tests/test_parser_contracts.py`` 가 덮습니다.

**스위트를 되살리는 것이 아닙니다.** 33,071줄이 지워진 이유는 부피였고, 그 판단을
되돌리지 않습니다. 여기 있는 것은 전부 introspection 이라 픽스처가 없고 네트워크를
타지 않으며, 각 검사는 **실제로 어긋난 적이 있는 것**에 대응합니다.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
import tomllib
from pathlib import Path
from typing import Any, get_args

import pytest

import korail_mobile_api
from korail_mobile_api import safety
from korail_mobile_api.redaction import is_sensitive_key


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "korail_mobile_api"


# ---------------------------------------------------------------------------
# 라우트 표
#
# 8ecd4ce: refunds.executeOnlineRefunds 가 두 표 **모두에** 없어서, 실제 돈을
# 옮기는 환불이 아무 라우트 검사도 없이 나갈 수 있었다. 배포 전에 손으로 발견됐다.
# ---------------------------------------------------------------------------


def test_every_mutation_route_has_a_registered_category() -> None:
    paths = {path for _method, path in safety.KORAIL_MUTATION_ROUTES}
    assert paths == set(safety.KORAIL_MUTATION_ROUTE_CATEGORIES)


def test_every_registered_category_is_a_declared_one() -> None:
    declared = set(get_args(safety.MutationCategory))
    assert set(safety.KORAIL_MUTATION_ROUTE_CATEGORIES.values()) <= declared


def test_the_two_route_tables_are_disjoint() -> None:
    """읽기 경로로 상태를 바꿀 수 없다는 것이 이 패키지의 중심 주장이다."""
    assert not (safety.KORAIL_READ_ONLY_ROUTES & safety.KORAIL_MUTATION_ROUTES)


def _route_literals_outside_safety() -> set[str]:
    found: set[str] = set()
    for path in SRC.glob("*.py"):
        if path.name == "safety.py":
            continue
        # v7_contract_data.py 는 생성물이라 작은따옴표를 쓴다. 둘 다 받는다.
        found.update(
            re.findall(r"""["'](/(?:classes|file|ebiz)[^"']*)["']""", path.read_text())
        )
    return found


@pytest.mark.parametrize(
    "route",
    sorted(
        {path for _m, path in safety.KORAIL_READ_ONLY_ROUTES}
        | {path for _m, path in safety.KORAIL_MUTATION_ROUTES}
    ),
)
def test_every_allowlisted_route_is_used_somewhere(route: str) -> None:
    """등록만 되고 부르는 데가 없는 라우트는 표에 있을 이유가 없다."""
    assert route in _route_literals_outside_safety()


# ---------------------------------------------------------------------------
# 공개면
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(korail_mobile_api.__all__))
def test_every_exported_name_exists(name: str) -> None:
    assert hasattr(korail_mobile_api, name)


def test_no_public_name_is_missing_from_all() -> None:
    import types

    public = {
        name
        for name in dir(korail_mobile_api)
        if not name.startswith("_")
        and not isinstance(getattr(korail_mobile_api, name), types.ModuleType)
    }
    assert public <= set(korail_mobile_api.__all__)


def test_all_has_no_duplicates() -> None:
    assert len(korail_mobile_api.__all__) == len(set(korail_mobile_api.__all__))


def test_version_agrees_with_pyproject() -> None:
    """``__init__.py:20-23`` 이 "이제 아무것도 지키지 않는다"고 적어 둔 것.

    pyproject 의 ``version`` 을 ``__version__`` 에서 파생시키면
    ``verify_distribution.py`` 가 깨진다(그쪽은 ``project["version"]`` 을 직접 읽는다).
    두 리터럴을 두고 여기서 맞추는 편이 싸다.
    """
    with (ROOT / "pyproject.toml").open("rb") as stream:
        declared = tomllib.load(stream)["project"]["version"]
    assert korail_mobile_api.__version__ == declared


# ---------------------------------------------------------------------------
# 마스킹 훑기
#
# ffb5189: CardPayment.card_password 와 card_expire 가 57일 동안 평문이었다.
# 와이어 키(hidVanPwd1)는 등록돼 있었고 **파이썬 속성명**이 빠져 있었다 --
# redact_value 가 데이터클래스를 field.name 으로 훑기 때문이다. 그때 있던 마스킹
# 테스트 658줄은 와이어 키 목록과 하드코딩된 이름 다섯 개만 훑어서 이것을 놓쳤다.
# 이 검사가 그 빠진 종류다.
# ---------------------------------------------------------------------------

_MODEL_MODULES = (
    "models",
    "read_models",
    "mutation_models",
    "limousine_models",
    "read_payloads",
)

_IDENTITY_SHAPED = re.compile(
    r"card|passw|pwd|birth|jumin|teln|phone|email|cust_?no|member_?no|pnr"
    r"|ret_?pwd|sale_?(dt|date|seq|window)",
    re.I,
)

#: 이름 모양은 걸리지만 민감한 값이 아닌 필드. **사유를 적지 않으면 넣을 수 없다.**
#: 새 필드가 여기에도 SENSITIVE_KEYS 에도 없으면 아래 검사가 떨어진다 -- 그것이
#: 이 목록의 목적이다. 값이 아니라 판단을 기록한다.
_NOT_SENSITIVE: dict[str, str] = {
    "railplus_cardinfo": "앱 전체 메인 캐시의 안내 문자열. 이용자의 카드가 아니다",
    "pwd_aes_cphd": "서버가 AES 를 원하는지의 Y/N 플래그. 비밀번호가 아니다",
    "card_type": "카드 브랜드 코드(예: J). 번호가 아니다",
    "card_kind_code": "할인카드 상품 종류 코드. 개인을 지목하지 않는다",
    "card_kind_management_no": "할인카드 상품 종류 관리번호. 상품 식별자이지 카드번호가 아니다",
    "email_verified_flag": "Y/N 플래그. 주소가 아니다",
    "phone_verified_flag": "Y/N 플래그. 번호가 아니다",
    "discount_card": "중첩 모델(DiscountCardOnTicket). 그 안의 card_no 가 따로 등록돼 있다",
    "card_refund_amount": "금액. 카드 식별자가 아니다",
}


def _model_dataclass_fields() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for module_name in _MODEL_MODULES:
        module = importlib.import_module(f"korail_mobile_api.{module_name}")
        for attribute in dir(module):
            obj: Any = getattr(module, attribute)
            if not (isinstance(obj, type) and dataclasses.is_dataclass(obj)):
                continue
            if obj.__module__ != module.__name__:
                continue
            rows.extend(
                (module_name, obj.__name__, field.name)
                for field in dataclasses.fields(obj)
            )
    return rows


def test_the_sweep_actually_reaches_the_models() -> None:
    """훑기가 비어 있으면 위 검사는 언제나 통과한다. 그 경우를 막는다."""
    rows = _model_dataclass_fields()
    assert len(rows) > 500
    assert any(name == "card_password" for _mod, _cls, name in rows)


@pytest.mark.parametrize(
    ("module_name", "class_name", "field_name"),
    [row for row in _model_dataclass_fields() if _IDENTITY_SHAPED.search(row[2])],
)
def test_identity_shaped_fields_are_registered_or_explained(
    module_name: str, class_name: str, field_name: str
) -> None:
    if field_name in _NOT_SENSITIVE:
        return
    assert is_sensitive_key(field_name), (
        f"{module_name}.{class_name}.{field_name} 은 신원 모양인데 "
        "SENSITIVE_KEYS 에도 _NOT_SENSITIVE 에도 없습니다. 가려야 하면 "
        "redaction.py 에 철자를 등록하고, 아니면 _NOT_SENSITIVE 에 사유를 적으십시오."
    )


def test_every_exemption_is_still_a_real_field() -> None:
    """모델에서 사라진 필드의 면제가 목록에 남아 있지 않게."""
    live = {name for _mod, _cls, name in _model_dataclass_fields()}
    assert set(_NOT_SENSITIVE) <= live


# ---------------------------------------------------------------------------
# 문서 색인 — docs/README.md 의 표는 손으로 유지한다고 그 파일 자신이 적는다
# ---------------------------------------------------------------------------

#: 문서 사이트의 원본. ``docs/README.md`` 가 표가 아니라 산문으로 따로 다룬다.
_SITE_PAGES = {"index.md", "quickstart.md", "safety.md", "errors.md", "changelog.md"}


def test_docs_index_lists_every_document() -> None:
    listed = set(
        re.findall(r"\|\s*\[[^\]]+\]\(([^)]+\.md)\)", (ROOT / "docs" / "README.md").read_text())
    )
    present = {
        path.name
        for path in (ROOT / "docs").glob("*.md")
        if path.name != "README.md" and path.name not in _SITE_PAGES
    }
    assert present == listed
