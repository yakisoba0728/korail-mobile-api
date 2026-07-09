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
