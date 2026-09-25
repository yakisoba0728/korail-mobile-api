"""Build actual PEP 517 archives offline; CI separately exercises build and twine.

These are package-policy tests, not assertions about Android application behavior.
The back end must already be installed: no implicit downloading or silent skips.
"""

from __future__ import annotations

import ast
import base64
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

pytestmark = pytest.mark.packaging
F8_ROOT = Path(__file__).resolve().parents[1]
F8_TOP_FILES = {"pyproject.toml", "MANIFEST.in", "README.md", "CHANGELOG.md", "LICENSE"}
F8_RECORD_MODULES = {"_maas_unsupported.py", "_social_login_unsupported.py", "_travel_search_unsupported.py"}
F8_SENTINEL = b"F8-FORBIDDEN-" + b"SYNTHETIC-CREDENTIAL-SENTINEL"


def _f8_version(source: bytes) -> str:
    tree = ast.parse(source)
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
    ]
    assert len(assignments) == 1
    value = ast.literal_eval(assignments[0].value)
    assert isinstance(value, str)
    return value


def _f8_safe_name(name: str) -> None:
    path = PurePosixPath(name)
    assert not path.is_absolute() and ".." not in path.parts
    assert not {"analysis", "__pycache__", ".git", ".github", ".venv"}.intersection(path.parts)
    lower = name.lower()
    assert path.suffix.lower() not in {
        ".apk",
        ".apks",
        ".aab",
        ".dex",
        ".so",
        ".dll",
        ".dylib",
        ".pyc",
        ".pyo",
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".jks",
        ".keystore",
    }
    assert not any(part == ".pypirc" or part.startswith(".env") for part in path.parts)
    assert not any(word in lower for word in ("credentials", "credential", "secrets"))


def _f8_backend(source: Path, out: Path, kind: str, env: dict[str, str]) -> Path:
    code = (
        "import sys; from setuptools import build_meta; "
        "fn = getattr(build_meta, 'build_' + sys.argv[1]); "
        "print('F8_ARTIFACT=' + fn(sys.argv[2])); "
        "assert 'korail_mobile_api' not in sys.modules, 'version resolution imported runtime code'"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code, kind, str(out)],
        cwd=source,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    artifact = next(
        line.split("=", 1)[1] for line in completed.stdout.splitlines() if line.startswith("F8_ARTIFACT=")
    )
    return out / artifact


@pytest.fixture
def f8_built_archives(tmp_path: Path, f8_subprocess_env: dict[str, str]) -> dict[str, Any]:
    """Copy only release inputs; inject forbidden synthetic files to test exclusion."""
    source = tmp_path / "source"
    source.mkdir()
    for name in F8_TOP_FILES:
        shutil.copy2(F8_ROOT / name, source / name)
    for name in ("src", "checks", "tests"):
        shutil.copytree(
            F8_ROOT / name, source / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info")
        )
    for name in (
        "analysis/secret.txt",
        "korail.apk",
        ".env",
        ".env.production",
        ".pypirc",
        "credentials.json",
        "src/korail_mobile_api/credentials.json",
        "src/korail_mobile_api/client.apk",
        "src/korail_mobile_api/.env",
        "checks/credentials.json",
        "tests/private.key",
    ):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(F8_SENTINEL)
    output = tmp_path / "dist"
    output.mkdir()
    sdist = _f8_backend(source, output, "sdist", f8_subprocess_env)
    direct_wheel = _f8_backend(source, output, "wheel", f8_subprocess_env)
    with zipfile.ZipFile(direct_wheel) as archive:
        direct_members = {name: archive.read(name) for name in archive.namelist()}
    # Build again from the sdist in a separate tree: no hidden source-tree dependency.
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with tarfile.open(sdist) as archive:
        members = archive.getmembers()
        for member in members:
            _f8_safe_name(member.name)
            assert member.isdir() or member.isfile(), "links/special files are forbidden"
        # Names/types have been checked explicitly, including on Python 3.11.
        if hasattr(tarfile, "data_filter"):
            archive.extractall(extracted, members=members, filter="data")
        else:
            archive.extractall(extracted, members=members)
    (sdist_root,) = extracted.iterdir()
    rebuilt_out = tmp_path / "rebuilt"
    rebuilt_out.mkdir()
    wheel = _f8_backend(sdist_root, rebuilt_out, "wheel", f8_subprocess_env)
    with tarfile.open(sdist) as archive:
        source_members = {
            str(PurePosixPath(member.name).relative_to(sdist_root.name)): archive.extractfile(member).read()
            for member in archive.getmembers()
            if member.isfile()
        }
    with zipfile.ZipFile(wheel) as archive:
        wheel_members = {name: archive.read(name) for name in archive.namelist()}
    return {"source": source_members, "wheel": wheel_members, "direct": direct_members}


def test_f8_distribution_contents_and_metadata(f8_built_archives: dict[str, Any]) -> None:
    """Fail closed on unexpected archive contents, dependency metadata or version drift."""
    source = f8_built_archives["source"]
    wheel = f8_built_archives["wheel"]
    direct = f8_built_archives["direct"]
    assert wheel.keys() == direct.keys()
    # RECORD bytes are also deterministic because files/metadata are identical.
    assert wheel == direct
    assert F8_TOP_FILES <= source.keys()
    assert "src/korail_mobile_api/py.typed" in source
    assert "korail_mobile_api/py.typed" in wheel
    for name in F8_RECORD_MODULES:
        assert "src/korail_mobile_api/" + name in source
        assert "korail_mobile_api/" + name in wheel
    for name in ("contract_api.py", "netfunnel_offline.py", "README.md", "ACCEPTANCE.md"):
        assert "checks/" + name in source
    for name in ("conftest.py", "test_public_api_smoke.py", "test_packaging.py"):
        assert "tests/" + name in source
    for name, data in wheel.items():
        _f8_safe_name(name)
        assert name.startswith("korail_mobile_api/") or ".dist-info/" in name
        assert not name.startswith(("checks/", "tests/"))
        assert F8_SENTINEL not in data
    for name, data in source.items():
        _f8_safe_name(name)
        assert name in F8_TOP_FILES | {"PKG-INFO", "setup.cfg"} or name.startswith(
            ("src/korail_mobile_api/", "src/korail_mobile_api.egg-info/", "checks/", "tests/")
        )
        assert F8_SENTINEL not in data
    # Runtime modules must be source modules only, plus the PEP 561 marker.
    expected_runtime = {
        "korail_mobile_api/" + path.name for path in (F8_ROOT / "src/korail_mobile_api").glob("*.py")
    }
    expected_runtime.add("korail_mobile_api/py.typed")
    assert {name for name in wheel if name.startswith("korail_mobile_api/")} == expected_runtime
    for name in expected_runtime:
        assert wheel[name] == source["src/" + name]
    project = tomllib.loads(source["pyproject.toml"].decode())
    assert project["project"]["dynamic"] == ["version"]
    assert "version" not in project["project"]
    assert project["tool"]["setuptools"]["dynamic"]["version"] == {"attr": "korail_mobile_api.__version__"}
    version = _f8_version(source["src/korail_mobile_api/__init__.py"])
    (metadata_name,) = [name for name in wheel if name.endswith(".dist-info/METADATA")]
    metadata = BytesParser().parsebytes(wheel[metadata_name])
    pkg_info = BytesParser().parsebytes(source["PKG-INFO"])
    assert metadata["Name"] == pkg_info["Name"] == "korail-mobile-api"
    assert metadata["Version"] == pkg_info["Version"] == version
    assert _f8_version(wheel["korail_mobile_api/__init__.py"]) == version
    assert metadata["Requires-Python"] == pkg_info["Requires-Python"] == ">=3.11"
    assert metadata["License-Expression"] == pkg_info["License-Expression"] == "Apache-2.0"
    assert metadata.get_all("License-File") == ["LICENSE"]
    assert metadata["Description-Content-Type"] == "text/markdown"
    assert metadata.get_payload(decode=True).decode("utf-8").rstrip() == source["README.md"].decode().rstrip()
    assert set(metadata.get_all("Classifier", [])) == set(project["project"]["classifiers"])
    expected_urls = {f"{key}, {value}" for key, value in project["project"]["urls"].items()}
    assert set(metadata.get_all("Project-URL", [])) == expected_urls
    requirements = [Requirement(text) for text in metadata.get_all("Requires-Dist", [])]
    runtime = {canonicalize_name(req.name): str(req.specifier) for req in requirements if req.marker is None}
    declared = {
        canonicalize_name(req.name): str(req.specifier)
        for req in map(Requirement, project["project"]["dependencies"])
    }
    assert runtime == declared
    assert set(runtime) == {"httpx", "cryptography"}
    for req in requirements:
        assert all(spec.operator == ">=" for spec in req.specifier), str(req)
    prefix = metadata_name.rsplit("/", 1)[0]
    assert wheel[prefix + "/licenses/LICENSE"] == source["LICENSE"]
    wheel_metadata = BytesParser().parsebytes(wheel[prefix + "/WHEEL"])
    assert wheel_metadata["Root-Is-Purelib"] == "true"
    assert wheel_metadata.get_all("Tag") == ["py3-none-any"]
    rows = list(csv.reader(io.StringIO(wheel[prefix + "/RECORD"].decode())))
    assert {row[0] for row in rows} == wheel.keys()
    for name, digest, size in rows:
        if name.endswith("/RECORD"):
            assert digest == size == ""
            continue
        assert int(size) == len(wheel[name])
        expected = base64.urlsafe_b64encode(hashlib.sha256(wheel[name]).digest()).rstrip(b"=").decode()
        assert digest == "sha256=" + expected


def test_f8_unsupported_modules_are_not_imported(f8_subprocess_env: dict[str, str]) -> None:
    """Record modules ship as source only, not as supported or normally loaded APIs."""
    code = (
        "import json,sys; sys.path.insert(0,sys.argv[1]); import korail_mobile_api as api; "
        "print(json.dumps([n for n in sys.modules if n.startswith('korail_mobile_api.')]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(F8_ROOT / "src")],
        env=f8_subprocess_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    modules = json.loads(result.stdout)
    for name in F8_RECORD_MODULES:
        assert "korail_mobile_api." + name.removesuffix(".py") not in modules
