# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""픽스처를 파서에 넣었을 때 나오는 **구조**를 얼립니다.

``ebc4d5f`` 가 지운 것 중 "parser regressions" 만 골든 픽스처가 없어서 남아
있었습니다. ``tests/test_invariants.py`` 는 introspection 만 하므로 파서가 응답을
어떻게 읽는지는 보지 못합니다. 이 파일이 그 자리를 채웁니다.

**값이 아니라 구조를 봅니다.** 픽스처의 값은 합성이라 언제든 다시 뜰 수 있지만,
파서가 어떤 모델을 만드는지·어떤 필드를 ``None`` 으로 두는지·목록을 몇 개로 읽는지는
계약입니다. ``h_arv_tm`` 을 ``h_dpt_tm`` 으로 잘못 읽으면 값은 그럴듯하지만 구조는
그대로라 잡히지 않습니다 — 그 종류는 필드 이름을 얼리는
``tests/test_form_contracts.py`` 쪽 일입니다.

픽스처 넷은 서버가 **실패**를 돌려준 응답입니다. 그중 셋은 파서가 예외를 냅니다.
실패도 계약이라 어떤 예외가 어떤 코드로 나오는지를 같이 얼립니다.

골든을 다시 뜨려면 ``KORAIL_GOLDEN_UPDATE=1 pytest`` — 그리고 **diff 를 읽으십시오.**
응답이 바뀐 것인지 파서가 깨진 것인지는 사람만 압니다.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from korail_mobile_api.models import BaseKorailResponse
from parser_map import PARSERS, WRAPPED


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "responses"
GOLDEN = Path(__file__).resolve().parent / "golden" / "parser_output.json"

#: 1차 비식별화가 한글을 뭉갤 때 쓴 음절. 이것만으로 이루어진 낱말은 사람 말이 아닙니다.
_SOUP_SYLLABLES = set("가나다라마바사아자차카타파하")

#: 대한민국의 경위도 범위. 1차 비식별화는 자릿수를 섞어 경도 ``843.94`` 를 남겼습니다.
_KOREA_LON = (126.0, 130.0)
_KOREA_LAT = (33.0, 39.0)

# 키 규칙은 한 번 틀렸습니다. 끝자리를 ``$`` 로 묶어 두었더니 ``h_dpt_tm_qb`` 의
# "94:45" 와 ``runDt1`` 의 "21145240" 이 통째로 빠져나갔습니다. 그렇다고 "포함"으로
# 넓히면 ``h_dtl_dsc_2`` 가 "dt 를 포함하니 날짜"가 되어 버립니다. 마디 경계를
# 명시하는 것이 그 사이입니다. ``re.IGNORECASE`` 를 쓰지 않는 것도 같은 이유로,
# ``Dt``/``DT``/``Date`` 는 저마다 다른 응답에서 오는 서로 다른 철자입니다.
_DATE_KEY = re.compile(r"(?:^|_)(?:dt|date|ymd)\d?$|(?:^|_)date_(?:start|end)$|Dt\d?$|DT$|Date$")
_TIME_KEY = re.compile(r"(?:^|_)(?:tm|time|hm)\d?(?:_qb)?$|Tm\d?$")
_MONEY_KEY = re.compile(r"(amt|fare|price|prc|pay|cash|won|chrg|cost)", re.IGNORECASE)
_COUNT_KEY = re.compile(r"(?:cnt|ordr|sqno|prnb)$", re.IGNORECASE)
_RATIO_KEY = re.compile(r"_rt$")

#: 원 단위 금액의 상한. 1차 비식별화는 자릿수를 섞어 운임 81조원을 남겼습니다.
_MONEY_CEILING = 10_000_000

#: 개수·순번의 상한. 한 편성의 좌석도, 조회 결과의 건수도, 역의 순번도 네 자리를
#: 넘지 않습니다. 1차 비식별화는 잔여석 305,082 석과 6억 건짜리 조회를 남겼습니다.
_COUNT_CEILING = 10_000


def _fixture_names() -> list[str]:
    return sorted(p.stem for p in FIXTURES.glob("*.json"))


@functools.cache
def _raw(name: str) -> Any:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def _load(name: str) -> Any:
    raw = _raw(name)
    return BaseKorailResponse.from_raw(raw) if name in WRAPPED else raw


def _signature(value: Any, path: str = "") -> dict[str, str]:
    """모델·컬렉션의 구조만 남깁니다 — 타입, ``None`` 여부, 길이. 값은 보지 않습니다."""
    out: dict[str, str] = {}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        out[path] = type(value).__name__
        for field in dataclasses.fields(value):
            if field.name == "raw":  # 파싱 전 원문이라 구조 계약이 아닙니다.
                continue
            out.update(_signature(getattr(value, field.name), f"{path}.{field.name}"))
    elif isinstance(value, (list, tuple)):
        out[path] = f"{type(value).__name__}[{len(value)}]"
        for index, item in enumerate(value):
            out.update(_signature(item, f"{path}[{index}]"))
    elif isinstance(value, dict):
        out[path] = f"dict[{len(value)}]"
        for key in sorted(value):
            out.update(_signature(value[key], f"{path}{{{key}}}"))
    else:
        out[path] = "None" if value is None else type(value).__name__
    return out


def _outcome(name: str) -> dict[str, Any]:
    """파싱이 되면 구조 서명을, 예외가 나면 그 예외를 기록합니다."""
    try:
        parsed = PARSERS[name](_load(name))
    except Exception as error:  # 어떤 예외가 나오는지가 바로 계약입니다.
        code = getattr(error, "code", None) or getattr(error, "message_code", None)
        return {"outcome": "raised", "error": type(error).__name__, "code": code}
    return {"outcome": "parsed", "signature": _signature(parsed)}


@functools.lru_cache(maxsize=1)
def _recorded() -> dict[str, Any]:
    if not GOLDEN.exists():
        return {}
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


if os.environ.get("KORAIL_GOLDEN_UPDATE") == "1":  # pragma: no cover - 사람이 부른다
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(
        json.dumps(
            {name: _outcome(name) for name in sorted(PARSERS)},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("name", sorted(PARSERS))
def test_the_parser_reads_the_fixture_into_the_same_shape(name: str) -> None:
    recorded = _recorded()
    assert name in recorded, (
        f"{name} 의 골든이 없습니다. 새 픽스처라면 "
        "KORAIL_GOLDEN_UPDATE=1 pytest 로 뜨고 diff 를 읽으십시오."
    )
    assert _outcome(name) == recorded[name]


def test_every_fixture_has_a_parser() -> None:
    """픽스처만 늘고 표가 따라오지 않으면 그 응답은 아무도 읽지 않습니다."""
    assert set(_fixture_names()) == set(PARSERS)


def test_the_golden_has_no_entry_for_a_fixture_that_is_gone() -> None:
    assert set(_recorded()) <= set(PARSERS)


def test_wrapped_names_are_all_real_fixtures() -> None:
    assert WRAPPED <= set(PARSERS)


# ---------------------------------------------------------------------------
# 비식별화가 다시 망가지는 것을 막는 가드.
#
# 1차 비식별화는 값을 같은 모양의 합성값으로 바꾸는 대신 자릿수와 음절을 뒤섞어
# 한국 밖의 좌표, 있을 수 없는 날짜, 조 단위 운임, 열네 음절짜리 한글 뭉치를
# 남겼습니다. 아래 넷은 그때 실제로 새어 나온 것들이고, 다음에 픽스처를 다시 뜰 때
# 같은 사고가 커밋되지 않게 막습니다.
# ---------------------------------------------------------------------------


def _strings(node: Any, path: str = "") -> list[tuple[str, str, str]]:
    """(경로, 키, 값) 을 모두 훑습니다."""
    found: list[tuple[str, str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                found.append((f"{path}.{key}", key, value))
            else:
                found.extend(_strings(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            found.extend(_strings(item, f"{path}[{index}]"))
    return found


@pytest.mark.parametrize("name", _fixture_names())
def test_no_fixture_value_is_syllable_soup(name: str) -> None:
    raw = _raw(name)
    soup = []
    for path, _key, value in _strings(raw):
        if value.startswith("합성"):  # 이 저장소가 스스로 넣은 대체값
            continue
        hangul = [c for c in value if "가" <= c <= "힣"]
        if not hangul or not all(c in _SOUP_SYLLABLES for c in hangul):
            continue
        # 낱말 전체가 수프이거나("자하파마다"), 숫자·라틴문자에 수프가 섞였거나
        # ("27,516라", "kep 4204 가하"). 뒤쪽은 한글이 두 자뿐이라 예전 규칙을
        # 빠져나갔습니다 -- 실제 역명 "각계"·"가남" 은 수프 아닌 음절을 지녀
        # 여기 걸리지 않습니다.
        if len(hangul) >= 3 or re.search(r"[0-9A-Za-z]", value):
            soup.append((path, value[:40]))
    assert not soup, f"{name}.json 에 뭉개진 한글이 남아 있습니다: {soup[:5]}"


@pytest.mark.parametrize("name", _fixture_names())
def test_every_coordinate_is_inside_korea(name: str) -> None:
    raw = _raw(name)
    for path, key, value in _strings(raw):
        low, high = {
            "longitude": _KOREA_LON,
            "latitude": _KOREA_LAT,
        }.get(key.lower(), (None, None))
        if low is None:
            continue
        assert low <= float(value) <= high, f"{name}.json {path} = {value}"


@pytest.mark.parametrize("name", _fixture_names())
def test_every_date_and_time_field_is_a_real_date_and_time(name: str) -> None:
    raw = _raw(name)
    for path, key, value in _strings(raw):
        # 8 자리는 날짜, 12/14 자리는 날짜에 시·분(·초) 가 붙은 것입니다.
        if _DATE_KEY.search(key) and re.fullmatch(r"\d{8}|\d{12}|\d{14}", value):
            date(int(value[:4]), int(value[4:6]), int(value[6:8]))  # 틀리면 ValueError
        if not _TIME_KEY.search(key):
            continue
        # ``h_dpt_tm`` 은 ``131139``, 그 거울인 ``h_dpt_tm_qb`` 는 ``13:11`` 입니다.
        parts = re.fullmatch(r"(\d{2})(\d{2})(\d{2})", value) or re.fullmatch(
            r"(\d{1,3}):(\d{2})(?::(\d{2}))?", value
        )
        if parts is None:
            continue
        hour, minute = int(parts.group(1)), int(parts.group(2))
        second = int(parts.group(3) or 0)
        # KORAIL 은 자정을 넘긴 운행을 24시 이후로 적습니다.
        assert hour <= 29 and minute < 60 and second < 60, f"{name}.json {path} = {value}"


@pytest.mark.parametrize("name", _fixture_names())
def test_no_amount_is_larger_than_a_train_fare_can_be(name: str) -> None:
    """운임은 원 단위로 다섯 자리입니다 — 열네 자리는 자릿수가 섞인 것입니다."""
    raw = _raw(name)
    for path, key, value in _strings(raw):
        if _MONEY_KEY.search(key) and re.fullmatch(r"-?\d+", value):
            assert abs(int(value)) < _MONEY_CEILING, f"{name}.json {path} = {value}"


@pytest.mark.parametrize("name", _fixture_names())
def test_no_count_or_ordinal_is_out_of_scale(name: str) -> None:
    """잔여석 305,082 석, 6억 건짜리 조회, 97 만 번째 정차역이 남아 있었습니다."""
    raw = _raw(name)
    for path, key, value in _strings(raw):
        if _COUNT_KEY.search(key) and re.fullmatch(r"\d+", value):
            assert int(value) < _COUNT_CEILING, f"{name}.json {path} = {value}"


@pytest.mark.parametrize("name", _fixture_names())
def test_every_ratio_is_a_percentage(name: str) -> None:
    """``-412.12`` 도 ``6721.20`` 도 비율이 아닙니다.

    ``h_train_disc_origin_rt`` 처럼 ``_rt`` 로 끝나면서 ``Y``/``N`` 을 담는 필드가
    있습니다. 숫자인 것만 봅니다 -- 그 철자가 왜 그런지는 따로 적어 두었습니다.
    """
    raw = _raw(name)
    for path, key, value in _strings(raw):
        if _RATIO_KEY.search(key) and re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            assert 0.0 <= float(value) <= 100.0, f"{name}.json {path} = {value}"
