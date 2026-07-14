from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path
import re
import stat
import sys
import tarfile
import tomllib
from typing import NamedTuple
import unicodedata
import zipfile


_FAILURE_MESSAGE = "distribution verification failed"
_MAX_DISPLAY_NAME = 96
_REQUIRED_SDIST_FILES = (
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "docs/RELEASE.md",
)
_FORBIDDEN_COMPONENT_FAMILIES = (
    ".ds_store",
    ".git",
    ".local-live-smoke.env",
    ".pytest_cache",
    ".worktrees",
    "__pycache__",
    "analysis",
    "build",
    "dist",
)
_FORBIDDEN_METADATA_HEADERS = (
    "License",
    "License-Expression",
    "Author",
    "Author-email",
    "Maintainer",
    "Maintainer-email",
    "Project-URL",
    "Home-page",
    "Download-URL",
)
_ALLOWED_ZIP_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_REQUIREMENT = re.compile(
    r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\s*\[[^\]]+\])?\s*(.*?)\s*\Z"
)


class ContractError(Exception):
    """Raised when a built distribution violates the internal release contract."""


class ProjectContract(NamedTuple):
    project_name: str
    version: str
    requires_python: str
    package_name: str
    normalized_project: str
    classifiers: tuple[str, ...]
    dependencies: tuple[str, ...]


def _normalize_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "_", value).casefold()


def _normalize_requirement(value: str) -> str | None:
    requirement, separator, marker = value.partition(";")
    if separator and re.search(r"\bextra\b", marker, flags=re.IGNORECASE):
        return None

    match = _REQUIREMENT.fullmatch(requirement)
    if match is None:
        raise ContractError
    name, extras, constraint = match.groups()
    normalized = _normalize_distribution_name(name)

    if extras:
        values = extras.strip()[1:-1].split(",")
        if not values or any(not value.strip() for value in values):
            raise ContractError
        normalized_extras = sorted(
            _normalize_distribution_name(value.strip()) for value in values
        )
        normalized += f"[{','.join(normalized_extras)}]"

    constraint = constraint.strip()
    if constraint.startswith("(") and constraint.endswith(")"):
        constraint = constraint[1:-1].strip()
    if constraint:
        specifiers = [part.strip() for part in constraint.split(",")]
        if any(not part for part in specifiers):
            raise ContractError
        normalized += ",".join(sorted(specifiers))

    if separator:
        normalized_marker = " ".join(marker.split())
        if not normalized_marker:
            raise ContractError
        normalized += f";{normalized_marker}"
    return normalized


def _project_contract() -> ProjectContract:
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

    project_name = project["name"]
    version = project["version"]
    requires_python = project["requires-python"]
    values = (project_name, version, requires_python, package_name)
    if not all(isinstance(value, str) and value for value in values):
        raise ContractError

    classifiers = project["classifiers"]
    dependencies = project.get("dependencies", [])
    if (
        not isinstance(classifiers, list)
        or not classifiers
        or any(not isinstance(value, str) or not value for value in classifiers)
        or len(set(classifiers)) != len(classifiers)
        or not isinstance(dependencies, list)
        or any(not isinstance(value, str) or not value for value in dependencies)
    ):
        raise ContractError
    normalized_dependencies = tuple(_normalize_requirement(value) for value in dependencies)
    if any(value is None for value in normalized_dependencies):
        raise ContractError
    if len(set(normalized_dependencies)) != len(normalized_dependencies):
        raise ContractError

    for forbidden in ("license", "authors", "maintainers", "urls"):
        if forbidden in project:
            raise ContractError

    return ProjectContract(
        project_name,
        version,
        requires_python,
        package_name,
        _normalize_distribution_name(project_name),
        tuple(classifiers),
        tuple(value for value in normalized_dependencies if value is not None),
    )


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


def _canonical_member_name(member_name: str) -> str:
    if (
        not member_name
        or "\\" in member_name
        or member_name.startswith("/")
        or _DRIVE_PREFIX.match(member_name)
        or any(unicodedata.category(character).startswith("C") for character in member_name)
    ):
        raise ContractError

    canonical = unicodedata.normalize("NFC", member_name)
    if canonical != member_name:
        raise ContractError
    if canonical.endswith("/"):
        canonical = canonical[:-1]
    components = canonical.split("/")
    if not canonical or any(component in {"", ".", ".."} for component in components):
        raise ContractError

    for component in components:
        lowered = component.casefold()
        if ".apk" in lowered or ".pyc" in lowered:
            raise ContractError
        for family in _FORBIDDEN_COMPONENT_FAMILIES:
            if lowered == family or lowered.startswith(
                (f"{family}.", f"{family}-", f"{family}_", f"{family}~")
            ):
                raise ContractError
    return canonical


def _zip_member_is_regular(member: zipfile.ZipInfo) -> bool:
    if member.is_dir():
        return False
    if member.create_system != 3:
        return True
    member_type = stat.S_IFMT(member.external_attr >> 16)
    return member_type in {0, stat.S_IFREG}


def _verify_metadata(payload: bytes, contract: ProjectContract) -> None:
    metadata = BytesParser(policy=policy.compat32).parsebytes(payload)
    if metadata.defects:
        raise ContractError
    for header, expected in (
        ("Name", contract.project_name),
        ("Version", contract.version),
        ("Requires-Python", contract.requires_python),
    ):
        values = metadata.get_all(header, [])
        if values != [expected]:
            raise ContractError

    classifiers = metadata.get_all("Classifier", [])
    if (
        len(classifiers) != len(contract.classifiers)
        or set(classifiers) != set(contract.classifiers)
    ):
        raise ContractError

    runtime_dependencies: list[str] = []
    for value in metadata.get_all("Requires-Dist", []):
        normalized = _normalize_requirement(value)
        if normalized is not None:
            runtime_dependencies.append(normalized)
    if (
        len(runtime_dependencies) != len(contract.dependencies)
        or set(runtime_dependencies) != set(contract.dependencies)
    ):
        raise ContractError

    if any(metadata.get_all(header) is not None for header in _FORBIDDEN_METADATA_HEADERS):
        raise ContractError


def _verify_wheel(wheel_path: Path, contract: ProjectContract) -> None:
    expected_dist_info = f"{contract.normalized_project}-{contract.version}.dist-info"
    metadata_path = f"{expected_dist_info}/METADATA"
    marker_path = f"{contract.package_name}/py.typed"

    with zipfile.ZipFile(wheel_path) as archive:
        members: dict[str, zipfile.ZipInfo] = {}
        for member in archive.infolist():
            name = _canonical_member_name(member.filename)
            if name in members:
                raise ContractError
            members[name] = member
            if member.flag_bits & 1 or member.compress_type not in _ALLOWED_ZIP_COMPRESSION:
                raise ContractError

            if member.is_dir():
                if member.create_system == 3:
                    member_type = stat.S_IFMT(member.external_attr >> 16)
                    if member_type not in {0, stat.S_IFDIR}:
                        raise ContractError
            elif not _zip_member_is_regular(member):
                raise ContractError

            for index, component in enumerate(name.split("/")):
                if component.endswith(".dist-info") and (
                    index != 0 or component != expected_dist_info
                ):
                    raise ContractError

        metadata_member = members.get(metadata_path)
        marker_member = members.get(marker_path)
        if (
            metadata_member is None
            or marker_member is None
            or not _zip_member_is_regular(metadata_member)
            or not _zip_member_is_regular(marker_member)
            or archive.read(marker_member) != b""
        ):
            raise ContractError
        _verify_metadata(archive.read(metadata_member), contract)


def _tar_payload(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    stream = archive.extractfile(member)
    if stream is None:
        raise ContractError
    return stream.read()


def _verify_sdist(sdist_path: Path, contract: ProjectContract) -> None:
    expected_root = f"{contract.normalized_project}-{contract.version}"
    metadata_path = f"{expected_root}/PKG-INFO"
    marker_path = f"{expected_root}/src/{contract.package_name}/py.typed"
    required_paths = {
        f"{expected_root}/{relative_path}" for relative_path in _REQUIRED_SDIST_FILES
    }

    with tarfile.open(sdist_path, mode="r:gz") as archive:
        members: dict[str, tarfile.TarInfo] = {}
        for member in archive.getmembers():
            name = _canonical_member_name(member.name)
            if name in members:
                raise ContractError
            members[name] = member
            if member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE}:
                raise ContractError
            if name == expected_root:
                if member.type != tarfile.DIRTYPE:
                    raise ContractError
            elif not name.startswith(f"{expected_root}/"):
                raise ContractError

        root_member = members.get(expected_root)
        metadata_member = members.get(metadata_path)
        marker_member = members.get(marker_path)
        if (
            root_member is None
            or root_member.type != tarfile.DIRTYPE
            or metadata_member is None
            or metadata_member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE}
            or marker_member is None
            or marker_member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE}
            or _tar_payload(archive, marker_member) != b""
        ):
            raise ContractError
        for required_path in required_paths:
            member = members.get(required_path)
            if member is None or member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE}:
                raise ContractError
        _verify_metadata(_tar_payload(archive, metadata_member), contract)


def _bounded_name(path: Path) -> str:
    name = re.sub(r"[^A-Za-z0-9._+\-]", "_", path.name)
    if len(name) > _MAX_DISPLAY_NAME:
        name = f"{name[: _MAX_DISPLAY_NAME - 3]}..."
    return name


def main(arguments: list[str] | None = None) -> int:
    try:
        wheel_path, sdist_path = _classify_artifacts(
            list(sys.argv[1:] if arguments is None else arguments)
        )
        contract = _project_contract()
        _verify_wheel(wheel_path, contract)
        _verify_sdist(sdist_path, contract)
    except Exception:
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
