from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CLASSIFIERS = {
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Typing :: Typed",
}


def test_internal_release_readiness_contract() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        configuration = tomllib.load(stream)

    project = configuration["project"]
    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.11"
    assert EXPECTED_CLASSIFIERS <= set(project["classifiers"])
    for forbidden_metadata in ("license", "authors", "maintainers", "urls"):
        assert forbidden_metadata not in project
    assert configuration["tool"]["setuptools"]["package-data"]["korail_mobile_api"] == [
        "py.typed"
    ]

    required_paths = (
        "src/korail_mobile_api/py.typed",
        "MANIFEST.in",
        "CHANGELOG.md",
        "SECURITY.md",
        "docs/RELEASE.md",
        "scripts/verify_distribution.py",
        ".github/workflows/ci.yml",
    )
    for relative_path in required_paths:
        assert (ROOT / relative_path).is_file(), relative_path

    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    for required_text in (
        "'3.11'",
        "'3.12'",
        "'3.13'",
        "'3.14'",
        "pytest -q",
        "python -m build",
        "verify_distribution.py",
        "python -m venv",
        "site-packages",
        "KorailClient",
    ):
        assert required_text in workflow

    release = (ROOT / "docs/RELEASE.md").read_text()
    release_lower = release.lower()
    assert "internal-only" in release_lower
    for blocker in ("license", "owner metadata", "canonical url", "explicit authorization"):
        assert blocker in release_lower
    assert "live tests" in release_lower and "forbidden" in release_lower
    assert "twine upload" not in release_lower
    assert "publish" not in release_lower

    readme = (ROOT / "README.md").read_text()
    handoff = (ROOT / "docs/NEXT_SESSION.md").read_text()
    for document in (readme, handoff):
        assert "25 routes" in document
        assert "28 public methods" in document
        assert "435 passed" in document and "1 skipped" in document
        assert "docs/RELEASE.md" in document

    guide = (ROOT / "docs/library-build-guide.md").read_text().lower()
    item_five = guide.split("5.", maxsplit=1)[1].split("6.", maxsplit=1)[0]
    assert "do not expose" in item_five
    assert "separate safety design" in item_five
    assert "explicit authorization" in item_five
