from __future__ import annotations

from email.parser import Parser
from pathlib import Path, PurePosixPath
import sys
import tarfile
import tomllib
import zipfile


_FAILURE_MESSAGE = "distribution verification failed"
_MAX_DISPLAY_NAME = 96
_REQUIRED_SDIST_FILES = (
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "docs/RELEASE.md",
)
_FORBIDDEN_COMPONENTS = {
    ".ds_store",
    ".git",
    ".local-live-smoke.env",
    ".pytest_cache",
    ".worktrees",
    "__pycache__",
    "analysis",
    "build",
    "dist",
}


class ContractError(Exception):
    """Raised when a built distribution violates the internal release contract."""


def _project_contract() -> tuple[str, str, str, str]:
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as stream:
        configuration = tomllib.load(stream)

    project = configuration["project"]
    package_data = configuration["tool"]["setuptools"]["package-data"]
    if len(package_data) != 1:
        raise ContractError

    package_name, marker_files = next(iter(package_data.items()))
    if marker_files != ["py.typed"]:
        raise ContractError

    values = (
        project["name"],
        project["version"],
        project["requires-python"],
        package_name,
    )
    if not all(isinstance(value, str) and value for value in values):
        raise ContractError
    return values


def _classify_artifacts(arguments: list[str]) -> tuple[Path, Path]:
    if len(arguments) != 2:
        raise ContractError

    wheels: list[Path] = []
    sdists: list[Path] = []
    for argument in arguments:
        artifact = Path(argument)
        if not artifact.is_file():
            raise ContractError
        if artifact.name.endswith(".whl"):
            wheels.append(artifact)
        elif artifact.name.endswith(".tar.gz"):
            sdists.append(artifact)
        else:
            raise ContractError

    if len(wheels) != 1 or len(sdists) != 1:
        raise ContractError
    return wheels[0], sdists[0]


def _reject_forbidden_members(member_names: list[str]) -> None:
    for member_name in member_names:
        normalized = member_name.replace("\\", "/")
        for component in PurePosixPath(normalized).parts:
            lowered = component.casefold()
            if lowered in _FORBIDDEN_COMPONENTS:
                raise ContractError
            if ".apk" in lowered or ".git" in lowered or lowered.endswith(".pyc"):
                raise ContractError


def _verify_wheel(
    wheel_path: Path,
    *,
    project_name: str,
    version: str,
    requires_python: str,
    package_name: str,
) -> None:
    with zipfile.ZipFile(wheel_path) as archive:
        member_names = archive.namelist()
        _reject_forbidden_members(member_names)

        if f"{package_name}/py.typed" not in member_names:
            raise ContractError

        metadata_members = [
            member_name
            for member_name in member_names
            if member_name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_members) != 1:
            raise ContractError

        metadata_text = archive.read(metadata_members[0]).decode("utf-8")
        metadata = Parser().parsestr(metadata_text)

    if metadata.get("Name") != project_name:
        raise ContractError
    if metadata.get("Version") != version:
        raise ContractError
    if metadata.get("Requires-Python") != requires_python:
        raise ContractError
    if "Typing :: Typed" not in metadata.get_all("Classifier", []):
        raise ContractError


def _contains_sdist_path(member_names: list[str], relative_path: str) -> bool:
    suffix = f"/{relative_path}"
    return any(
        member_name == relative_path or member_name.endswith(suffix)
        for member_name in member_names
    )


def _verify_sdist(sdist_path: Path, *, package_name: str) -> None:
    with tarfile.open(sdist_path, mode="r:*") as archive:
        member_names = [member.name for member in archive.getmembers()]

    _reject_forbidden_members(member_names)

    marker_paths = (
        f"src/{package_name}/py.typed",
        f"{package_name}/py.typed",
    )
    if not any(
        _contains_sdist_path(member_names, marker_path)
        for marker_path in marker_paths
    ):
        raise ContractError

    for required_file in _REQUIRED_SDIST_FILES:
        if not _contains_sdist_path(member_names, required_file):
            raise ContractError


def _bounded_name(path: Path) -> str:
    name = path.name
    if len(name) <= _MAX_DISPLAY_NAME:
        return name
    return f"{name[: _MAX_DISPLAY_NAME - 3]}..."


def main(arguments: list[str] | None = None) -> int:
    try:
        wheel_path, sdist_path = _classify_artifacts(
            list(sys.argv[1:] if arguments is None else arguments)
        )
        project_name, version, requires_python, package_name = _project_contract()
        _verify_wheel(
            wheel_path,
            project_name=project_name,
            version=version,
            requires_python=requires_python,
            package_name=package_name,
        )
        _verify_sdist(sdist_path, package_name=package_name)
    except (
        ContractError,
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ):
        print(_FAILURE_MESSAGE, file=sys.stderr)
        return 1

    print(
        "distribution contract verified: "
        f"wheel={_bounded_name(wheel_path)} "
        f"sdist={_bounded_name(sdist_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
