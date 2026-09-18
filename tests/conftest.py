# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

import json
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_json_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def load_json_fixture(name: str) -> dict:
    return _load_json_fixture(name)


@pytest.fixture(name="load_json_fixture")
def load_json_fixture_fixture():
    return _load_json_fixture
