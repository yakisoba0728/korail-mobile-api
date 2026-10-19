"""Validate manual and automatic workflows without running them or accessing the network."""

import subprocess
import sys
from pathlib import Path
from shutil import which

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not (ROOT / ".github/workflows").is_dir(), reason="workflows are not shipped in sdist")
def test_actionlint_checks_all_workflows(f8_subprocess_env):
    executable = which("actionlint", path=str(Path(sys.executable).parent))
    assert executable is not None, "Install the declared dev dependencies before running tests"
    result = subprocess.run(
        [str(executable), "-shellcheck=", "-pyflakes="],
        cwd=ROOT,
        env=f8_subprocess_env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
