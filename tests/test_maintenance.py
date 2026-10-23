"""Validate manual and automatic workflows without running them or accessing the network."""

import io
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from shutil import which

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

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


@pytest.mark.skipif(not (ROOT / ".github/workflows").is_dir(), reason="workflows are not shipped in sdist")
def test_workflow_embedded_python_compiles() -> None:
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        source = path.read_text(encoding="utf-8")
        for indent, body, end_indent in re.findall(r"(?ms)^( +)python - <<'PY'\n(.*?)^( +)PY(?:\n|$)", source):
            assert indent == end_indent, f"{path}: heredoc terminator must match shell indentation"
            lines = body.splitlines()
            assert all(not line.strip() or line.startswith(indent) for line in lines), path
            compile("\n".join(line[len(indent) :] for line in lines), str(path), "exec")


@pytest.mark.skipif(not (ROOT / ".github/workflows").is_dir(), reason="workflows are not shipped in sdist")
def test_publish_consumes_same_run_installed_wheel_artifact() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    publish = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    jobs = publish.split("jobs:\n", 1)[1]
    assert re.findall(r"(?m)^  ([\w-]+):", jobs) == ["verify-ref", "ci", "publish"]
    assert "    needs: verify-ref\n    uses: ./.github/workflows/ci.yml\n" in jobs
    assert "if os.environ['GITHUB_REF_TYPE'] != 'tag':" in jobs
    assert "if tag != f'v{version}':" in jobs
    publisher = jobs.split("  publish:\n", 1)[1]
    assert "    needs: ci\n" in publisher
    assert "    if:" not in publisher and "continue-on-error:" not in ci + publish
    assert "on:\n  workflow_dispatch:\n\npermissions:\n  contents: read\n" in publish
    assert "      id-token: write\n" in publisher and "      name: pypi\n" in publisher
    assert "  cancel-in-progress: false\n" in publish
    steps = publisher.split("    steps:\n", 1)[1]
    assert re.findall(r"uses: ([^@]+)@", steps) == [
        "actions/download-artifact",
        "pypa/gh-action-pypi-publish",
    ]
    assert "          name: validated-dist\n          path: dist/\n" in steps
    assert not any(key in steps for key in ("run:", "run-id:", "github-token:", "repository:"))
    assert "    if:" not in steps
    for workflow in (ci, publish):
        for action in re.findall(r"uses: ([^\s]+)", workflow):
            assert action == "./.github/workflows/ci.yml" or re.fullmatch(r"[^@]+@[0-9a-f]{40}", action), action

    assert re.findall(r"(?m)^  ([\w-]+):", ci.split("jobs:\n", 1)[1]) == ["verify", "maintenance", "docs"]
    assert "            dependencies: minimum\n" in ci
    assert "if Requirement(text).name == 'mypy'" in ci
    assert "scanners: vuln,secret,misconfig" in ci and "python -m mkdocs build --strict" in ci
    verify = ci.split("  verify:\n", 1)[1].split("\n  maintenance:\n", 1)[0]
    verify_steps = re.split(r"(?m)^      - ", verify)[1:]
    installed_index = next(i for i, step in enumerate(verify_steps) if "run installed-package checks" in step)
    upload = verify_steps[-1]
    assert installed_index == len(verify_steps) - 2
    assert upload.startswith("name: Save validated distributions\n")
    assert "if: matrix.python == '3.14' && matrix.dependencies == 'current'\n" in upload
    assert "uses: actions/upload-artifact@" in upload
    assert (
        "          name: validated-dist\n          path: dist/\n          if-no-files-found: error\n" in upload
    )
    assert "python -m twine check --strict dist/*" in verify


def test_mypy_minimum_and_configuration_support_requested_error_codes(monkeypatch) -> None:
    from mypy.config_parser import parse_config_file
    from mypy.options import Options

    path = ROOT / "pyproject.toml"
    project = tomllib.loads(path.read_text(encoding="utf-8"))
    (requirement,) = (
        req
        for text in project["project"]["optional-dependencies"]["dev"]
        if (req := Requirement(text)).name == "mypy"
    )
    (bound,) = requirement.specifier
    assert bound.operator == ">=" and Version(bound.version) >= Version("1.18.1")
    monkeypatch.setenv("MYPY_CONFIG_FILE_DIR", str(ROOT))
    options = Options()
    stderr = io.StringIO()
    parse_config_file(options, lambda: None, str(path), stderr=stderr)
    assert stderr.getvalue() == ""
    assert set(options.enable_error_code) == set(project["tool"]["mypy"]["enable_error_code"])


@pytest.mark.skipif(not (ROOT / ".github/workflows").is_dir(), reason="workflows are not shipped in sdist")
def test_docs_job_runs_griffe_regressions_before_strict_build() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    docs = ci.split("  docs:\n", 1)[1]
    assert "python -m pip install -e '.[dev]' -r docs/requirements.txt" in docs
    assert docs.index('python -c "import griffe"') < docs.index("python -m pytest tests/test_docs.py --no-cov")
    assert docs.index("python -m pytest tests/test_docs.py --no-cov") < docs.index(
        "python -m mkdocs build --strict"
    )
    assert "continue-on-error:" not in docs and "    if:" not in docs
    assert "python -m ruff check src checks tests docs/griffe_docs.py" in ci
    assert "python -m ruff format --check src checks tests docs/griffe_docs.py" in ci
