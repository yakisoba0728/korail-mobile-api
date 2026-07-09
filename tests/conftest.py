import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_json_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
