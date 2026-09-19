# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""What the offline CI workflow actually runs.

CONTRIBUTING promises that CI runs the same gates a contributor runs: the
offline suite, ruff and pyright, plus the strict site build. A workflow that
quietly dropped the "not live" marker, a job, or the Python floor would still
show green, because it would simply check less. This reads the workflow and
holds it to those promises, deriving the version list from pyproject.toml
rather than repeating it.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).parents[1]


def _workflow() -> dict[str, Any]:
    return yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


def _pyproject() -> dict[str, Any]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _runs(job: dict[str, Any]) -> list[str]:
    return [step["run"].strip() for step in job["steps"] if "run" in step]


def test_ci_runs_the_four_gates_with_the_extras_that_carry_them():
    jobs = _workflow()["jobs"]
    assert _runs(jobs["test"]) == [
        'python -m pip install -e ".[test]"',
        'pytest -q -m "not live"',
    ]
    assert _runs(jobs["lint"]) == ['python -m pip install -e ".[dev]"', "ruff check ."]
    assert _runs(jobs["types"]) == ['python -m pip install -e ".[dev]"', "pyright"]
    assert _runs(jobs["docs"]) == [
        'python -m pip install -e ".[docs]"',
        "mkdocs build --strict",
    ]


def test_ci_tests_every_supported_python_and_all_three_systems():
    pyproject = _pyproject()
    supported = {
        classifier.rsplit(" :: ", 1)[1]
        for classifier in pyproject["project"]["classifiers"]
        if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", classifier)
    }
    matrix = _workflow()["jobs"]["test"]["strategy"]["matrix"]
    rows = [(os, version) for os in matrix["os"] for version in matrix["python-version"]]
    rows += [(extra["os"], extra["python-version"]) for extra in matrix.get("include", [])]

    assert {version for _, version in rows} == supported
    assert {os for os, _ in rows} == {"ubuntu-latest", "macos-latest", "windows-latest"}
    # The floor is what requires-python states and what pyright analyses.
    floor = min(supported, key=lambda version: tuple(map(int, version.split("."))))
    assert pyproject["project"]["requires-python"] == f">={floor}"
    assert pyproject["tool"]["pyright"]["pythonVersion"] == floor
    types_python = [
        step["with"]["python-version"]
        for step in _workflow()["jobs"]["types"]["steps"]
        if "with" in step and "python-version" in step["with"]
    ]
    assert types_python == [floor]


def test_ci_only_reads_the_repository():
    workflow = _workflow()
    assert workflow["permissions"] == {"contents": "read"}
    for job in workflow["jobs"].values():
        assert "permissions" not in job
