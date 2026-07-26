from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
from pathlib import Path
import os
import re
import stat
import struct
import subprocess
import sys
import tarfile
import tomllib
import warnings
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "korail_mobile_api"
PROJECT_NAME = "korail-mobile-api"
EXPECTED_KEYWORDS = ['korail','read-only-by-default','mobile-api']
LIVE_ENV = "KORAIL_MOBILE_API_LIVE"
CLIENT_NAME = "KorailClient"
FAILURE_MESSAGE = "distribution verification failed\n"
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
FORBIDDEN_METADATA_HEADERS = (
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

with (ROOT / "pyproject.toml").open("rb") as stream:
    CONFIGURATION = tomllib.load(stream)
PROJECT = CONFIGURATION["project"]
VERSION = PROJECT["version"]
REQUIRES_PYTHON = PROJECT["requires-python"]
DEPENDENCIES = list(PROJECT["dependencies"])
NORMALIZED_PROJECT = re.sub(r"[-_.]+", "_", PROJECT_NAME).casefold()
DIST_INFO = f"{NORMALIZED_PROJECT}-{VERSION}.dist-info"
SDIST_ROOT = f"{NORMALIZED_PROJECT}-{VERSION}"

SPEC = spec_from_file_location(
    f"_verify_distribution_{PACKAGE_NAME}",
    ROOT / "scripts/verify_distribution.py",
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def _metadata(
    *,
    singletons: dict[str, list[str]] | None = None,
    classifiers: list[str] | None = None,
    dependencies: list[str] | None = None,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> bytes:
    singleton_values = {
        "Name": [PROJECT_NAME],
        "Version": [VERSION],
        "Requires-Python": [REQUIRES_PYTHON],
    }
    if singletons:
        singleton_values.update(singletons)

    lines = ["Metadata-Version: 2.4"]
    for header in ("Name", "Version", "Requires-Python"):
        lines.extend(f"{header}: {value}" for value in singleton_values[header])
    lines.extend(
        f"Classifier: {value}"
        for value in (
            sorted(EXPECTED_CLASSIFIERS) if classifiers is None else classifiers
        )
    )
    lines.extend(
        f"Requires-Dist: {value}"
        for value in (DEPENDENCIES if dependencies is None else dependencies)
    )
    lines.extend(f"{header}: {value}" for header, value in extra_headers)
    return ("\n".join(lines) + "\n\n").encode()


def _zip_info(name: str, mode: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = (mode | 0o644) << 16
    info.compress_type = zipfile.ZIP_STORED
    return info


def _write_wheel(
    directory: Path,
    *,
    metadata: bytes | None = None,
    include_metadata: bool = True,
    marker: bytes | None = b"",
    marker_info: zipfile.ZipInfo | None = None,
    dist_info: str = DIST_INFO,
    extra_names: tuple[str, ...] = (),
    extra_infos: tuple[zipfile.ZipInfo, ...] = (),
    duplicate_name: str | None = None,
    compression: int = zipfile.ZIP_DEFLATED,
    filename: str | None = None,
) -> Path:
    path = directory / (
        filename or f"{NORMALIZED_PROJECT}-{VERSION}-py3-none-any.whl"
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, mode="w", compression=compression) as archive:
            if marker is not None:
                if marker_info is None:
                    archive.writestr(f"{PACKAGE_NAME}/py.typed", marker)
                else:
                    archive.writestr(marker_info, marker)
            if include_metadata:
                archive.writestr(
                    f"{dist_info}/METADATA",
                    _metadata() if metadata is None else metadata,
                )
            for name in extra_names:
                archive.writestr(name, b"extra")
            for info in extra_infos:
                archive.writestr(info, b"target")
            if duplicate_name is not None:
                archive.writestr(duplicate_name, b"first")
                archive.writestr(duplicate_name, b"second")
    return path


def _tar_info(
    name: str,
    *,
    member_type: bytes = tarfile.REGTYPE,
    data: bytes = b"",
    linkname: str = "",
) -> tuple[tarfile.TarInfo, bytes]:
    info = tarfile.TarInfo(name)
    info.type = member_type
    info.mode = 0o644
    info.linkname = linkname
    if member_type in {tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.CONTTYPE}:
        info.size = len(data)
    return info, data


def _write_sdist(
    directory: Path,
    *,
    metadata: bytes | None = None,
    include_metadata: bool = True,
    marker: bytes | None = b"",
    missing: tuple[str, ...] = (),
    root: str = SDIST_ROOT,
    extra_members: tuple[tuple[tarfile.TarInfo, bytes], ...] = (),
    overrides: dict[str, tuple[bytes, bytes, str]] | None = None,
    duplicate_name: str | None = None,
    gzip: bool = True,
) -> Path:
    path = directory / f"{NORMALIZED_PROJECT}-{VERSION}.tar.gz"
    files: dict[str, bytes] = {
        "README.md": b"readme\n",
        "CHANGELOG.md": b"changelog\n",
        "SECURITY.md": b"security\n",
        "docs/RELEASE.md": b"release\n",
        f"src/{PACKAGE_NAME}/py.typed": b"" if marker is None else marker,
        "PKG-INFO": _metadata() if metadata is None else metadata,
    }
    if marker is None:
        files.pop(f"src/{PACKAGE_NAME}/py.typed")
    if not include_metadata:
        files.pop("PKG-INFO")
    for relative_path in missing:
        files.pop(relative_path, None)

    mode = "w:gz" if gzip else "w"
    with tarfile.open(path, mode=mode) as archive:
        root_info = tarfile.TarInfo(root)
        root_info.type = tarfile.DIRTYPE
        root_info.mode = 0o755
        archive.addfile(root_info)

        override_values = overrides or {}
        for relative_path, data in files.items():
            if relative_path in override_values:
                member_type, override_data, linkname = override_values[relative_path]
                info, payload = _tar_info(
                    f"{root}/{relative_path}",
                    member_type=member_type,
                    data=override_data,
                    linkname=linkname,
                )
            else:
                info, payload = _tar_info(f"{root}/{relative_path}", data=data)
            archive.addfile(
                info,
                BytesIO(payload)
                if info.type in {
                    tarfile.REGTYPE,
                    tarfile.AREGTYPE,
                    tarfile.CONTTYPE,
                }
                else None,
            )

        for info, payload in extra_members:
            archive.addfile(
                info,
                BytesIO(payload)
                if info.type in {
                    tarfile.REGTYPE,
                    tarfile.AREGTYPE,
                    tarfile.CONTTYPE,
                }
                else None,
            )

        if duplicate_name is not None:
            for payload in (b"first", b"second"):
                info, data = _tar_info(duplicate_name, data=payload)
                archive.addfile(info, BytesIO(data))
    return path


def _valid_pair(directory: Path) -> tuple[Path, Path]:
    return _write_wheel(directory), _write_sdist(directory)


def _assert_rejected(
    capsys: pytest.CaptureFixture[str],
    arguments: list[Path | str],
) -> None:
    try:
        exit_code = VERIFIER.main([str(argument) for argument in arguments])
    except Exception as error:
        pytest.fail(f"ordinary exception escaped CLI boundary: {type(error).__name__}")
    captured = capsys.readouterr()
    assert exit_code != 0
    assert captured.out == ""
    assert captured.err == FAILURE_MESSAGE


def _pair_with_metadata(
    directory: Path,
    target: str,
    metadata: bytes,
) -> tuple[Path, Path]:
    wheel = _write_wheel(
        directory,
        metadata=metadata if target == "wheel" else _metadata(),
    )
    sdist = _write_sdist(
        directory,
        metadata=metadata if target == "sdist" else _metadata(),
    )
    return wheel, sdist


def _mark_zip_encrypted(path: Path) -> None:
    data = bytearray(path.read_bytes())
    for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        start = 0
        while True:
            position = data.find(signature, start)
            if position < 0:
                break
            flags = struct.unpack_from("<H", data, position + flag_offset)[0]
            struct.pack_into("<H", data, position + flag_offset, flags | 1)
            start = position + len(signature)
    path.write_bytes(data)


def test_source_release_metadata_is_exact() -> None:
    assert PROJECT["name"] == PROJECT_NAME
    assert PROJECT["version"] == "0.2.0"
    assert PROJECT["requires-python"] == ">=3.11"
    assert PROJECT["keywords"] == EXPECTED_KEYWORDS
    assert set(PROJECT["classifiers"]) == EXPECTED_CLASSIFIERS
    assert len(PROJECT["classifiers"]) == len(EXPECTED_CLASSIFIERS)
    for forbidden in ("license", "authors", "maintainers", "urls"):
        assert forbidden not in PROJECT
    assert CONFIGURATION["tool"]["setuptools"]["package-data"][PACKAGE_NAME] == [
        "py.typed"
    ]

    marker = ROOT / "src" / PACKAGE_NAME / "py.typed"
    assert marker.is_file()
    assert marker.read_bytes() == b""
    for relative_path in (
        "MANIFEST.in",
        "CHANGELOG.md",
        "SECURITY.md",
        "docs/RELEASE.md",
        "scripts/verify_distribution.py",
        ".github/workflows/ci.yml",
    ):
        assert (ROOT / relative_path).is_file()


def test_valid_pair_is_accepted_in_either_argument_order(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel, sdist = _valid_pair(tmp_path)
    assert VERIFIER.main([str(sdist), str(wheel)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == (
        "distribution contract verified: "
        f"wheel={wheel.name} sdist={sdist.name}\n"
    )


def test_rejects_wrong_argument_count_and_artifact_types(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel, sdist = _valid_pair(tmp_path)
    unexpected = tmp_path / "unexpected.zip"
    unexpected.write_bytes(b"not an artifact")
    for arguments in (
        [],
        [wheel],
        [wheel, wheel],
        [sdist, sdist],
        [wheel, sdist, unexpected],
        [wheel, unexpected],
    ):
        _assert_rejected(capsys, list(arguments))


NONCANONICAL_NAMES = (
    r"segment\backslash.txt",
    "/absolute.txt",
    "C:/drive.txt",
    "segment//empty.txt",
    "segment/./dot.txt",
    "segment/../traversal.txt",
    "segment/control\x01.txt",
)


@pytest.mark.parametrize("archive_kind", ("wheel", "sdist"))
@pytest.mark.parametrize("bad_name", NONCANONICAL_NAMES)
def test_rejects_noncanonical_archive_member_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    archive_kind: str,
    bad_name: str,
) -> None:
    wheel, sdist = _valid_pair(tmp_path)
    name = bad_name.encode().decode("unicode_escape")
    if archive_kind == "wheel":
        wheel.unlink()
        wheel = _write_wheel(tmp_path, extra_names=(name,))
    else:
        sdist.unlink()
        if not name.startswith("/") and not re.match(r"^[A-Za-z]:", name):
            name = f"{SDIST_ROOT}/{name}"
        info, data = _tar_info(name, data=b"bad")
        sdist = _write_sdist(tmp_path, extra_members=((info, data),))
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("archive_kind", ("wheel", "sdist"))
def test_rejects_duplicate_normalized_member_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    archive_kind: str,
) -> None:
    wheel, sdist = _valid_pair(tmp_path)
    if archive_kind == "wheel":
        wheel.unlink()
        wheel = _write_wheel(tmp_path, duplicate_name="duplicate.txt")
    else:
        sdist.unlink()
        sdist = _write_sdist(
            tmp_path,
            duplicate_name=f"{SDIST_ROOT}/README.md",
        )
    _assert_rejected(capsys, [wheel, sdist])


FORBIDDEN_MEMBER_COMPONENTS = (
    ".local-live-smoke.env",
    ".local-live-smoke.env.backup",
    "application.apk",
    "application.apk.bak",
    ".DS_Store",
    ".DS_Store.backup",
    ".worktrees",
    ".worktrees.old",
    ".git",
    ".git.backup",
    "analysis",
    "analysis-copy",
    "build",
    "build_old",
    "dist",
    "dist~",
    ".pytest_cache",
    ".pytest_cache.backup",
    "__pycache__",
    "__pycache__.old",
    "module.pyc",
    "module.pyc.backup",
)


@pytest.mark.parametrize("archive_kind", ("wheel", "sdist"))
@pytest.mark.parametrize("component", FORBIDDEN_MEMBER_COMPONENTS)
def test_rejects_every_forbidden_member_family_and_backup_variant(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    archive_kind: str,
    component: str,
) -> None:
    wheel, sdist = _valid_pair(tmp_path)
    if archive_kind == "wheel":
        wheel.unlink()
        wheel = _write_wheel(tmp_path, extra_names=(f"safe/{component}",))
    else:
        sdist.unlink()
        info, data = _tar_info(
            f"{SDIST_ROOT}/safe/{component}",
            data=b"bad",
        )
        sdist = _write_sdist(tmp_path, extra_members=((info, data),))
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize(
    "mode",
    (
        stat.S_IFLNK,
        stat.S_IFIFO,
        stat.S_IFCHR,
        stat.S_IFBLK,
        stat.S_IFSOCK,
    ),
)
def test_rejects_zip_links_and_special_member_types(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mode: int,
) -> None:
    wheel = _write_wheel(
        tmp_path,
        extra_infos=(_zip_info("special-member", mode),),
    )
    sdist = _write_sdist(tmp_path)
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize(
    "member_type",
    (
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
        tarfile.FIFOTYPE,
        tarfile.CONTTYPE,
    ),
)
def test_rejects_tar_links_devices_fifos_and_special_types(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    member_type: bytes,
) -> None:
    wheel = _write_wheel(tmp_path)
    info, data = _tar_info(
        f"{SDIST_ROOT}/special-member",
        member_type=member_type,
        data=b"bad",
        linkname="target",
    )
    sdist = _write_sdist(tmp_path, extra_members=((info, data),))
    _assert_rejected(capsys, [wheel, sdist])


def test_rejects_non_gzip_sdist_with_tar_gz_suffix(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = _write_wheel(tmp_path)
    sdist = _write_sdist(tmp_path, gzip=False)
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("root_mode", ("wrong", "multiple"))
def test_requires_one_exact_project_version_sdist_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    root_mode: str,
) -> None:
    wheel = _write_wheel(tmp_path)
    if root_mode == "wrong":
        sdist = _write_sdist(tmp_path, root="wrong-project-9.9.9")
    else:
        extra_root = tarfile.TarInfo("other-root")
        extra_root.type = tarfile.DIRTYPE
        sdist = _write_sdist(tmp_path, extra_members=((extra_root, b""),))
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
@pytest.mark.parametrize("marker_state", ("missing", "nonempty", "special"))
def test_requires_regular_zero_byte_typed_markers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    marker_state: str,
) -> None:
    wheel, sdist = _valid_pair(tmp_path)
    if target == "wheel":
        wheel.unlink()
        if marker_state == "special":
            info = _zip_info(f"{PACKAGE_NAME}/py.typed", stat.S_IFLNK)
            wheel = _write_wheel(tmp_path, marker=b"target", marker_info=info)
        else:
            wheel = _write_wheel(
                tmp_path,
                marker=None if marker_state == "missing" else b"not empty",
            )
    else:
        sdist.unlink()
        if marker_state == "special":
            sdist = _write_sdist(
                tmp_path,
                overrides={
                    f"src/{PACKAGE_NAME}/py.typed": (
                        tarfile.SYMTYPE,
                        b"",
                        "target",
                    )
                },
            )
        else:
            sdist = _write_sdist(
                tmp_path,
                marker=None if marker_state == "missing" else b"not empty",
            )
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize(
    "required_document",
    ("README.md", "CHANGELOG.md", "SECURITY.md", "docs/RELEASE.md"),
)
def test_requires_each_exact_regular_sdist_document(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    required_document: str,
) -> None:
    wheel = _write_wheel(tmp_path)
    sdist = _write_sdist(tmp_path, missing=(required_document,))
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
@pytest.mark.parametrize(
    ("header", "expected", "wrong"),
    (
        ("Name", PROJECT_NAME, "wrong-project"),
        ("Version", VERSION, "9.9.9"),
        ("Requires-Python", REQUIRES_PYTHON, ">=99"),
    ),
)
@pytest.mark.parametrize("problem", ("missing", "duplicate", "wrong"))
def test_rejects_missing_duplicate_or_wrong_singleton_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    header: str,
    expected: str,
    wrong: str,
    problem: str,
) -> None:
    if problem == "missing":
        values = []
    elif problem == "duplicate":
        values = [expected, expected]
    else:
        values = [wrong]
    wheel, sdist = _pair_with_metadata(
        tmp_path,
        target,
        _metadata(singletons={header: values}),
    )
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
@pytest.mark.parametrize("problem", ("missing", "extra", "duplicate"))
def test_requires_the_exact_classifier_set_without_duplicates(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    problem: str,
) -> None:
    classifiers = sorted(EXPECTED_CLASSIFIERS)
    if problem == "missing":
        classifiers.remove("Programming Language :: Python :: 3.14")
    elif problem == "extra":
        classifiers.append("Operating System :: OS Independent")
    else:
        classifiers.append(classifiers[0])
    wheel, sdist = _pair_with_metadata(
        tmp_path,
        target,
        _metadata(classifiers=classifiers),
    )
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
@pytest.mark.parametrize("problem", ("missing", "extra", "duplicate"))
def test_requires_the_exact_normalized_runtime_dependency_set(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    problem: str,
) -> None:
    dependencies = list(DEPENDENCIES)
    if problem == "missing":
        dependencies = dependencies[1:]
    elif problem == "extra":
        dependencies.append("unexpected-package>=1")
    else:
        dependencies.append(dependencies[0])
    wheel, sdist = _pair_with_metadata(
        tmp_path,
        target,
        _metadata(dependencies=dependencies),
    )
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
@pytest.mark.parametrize("header", FORBIDDEN_METADATA_HEADERS)
def test_rejects_forbidden_owner_license_and_url_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    header: str,
) -> None:
    wheel, sdist = _pair_with_metadata(
        tmp_path,
        target,
        _metadata(extra_headers=((header, "forbidden value"),)),
    )
    _assert_rejected(capsys, [wheel, sdist])


def test_requires_exact_dist_info_metadata_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = _write_wheel(tmp_path, dist_info="wrong_project-9.9.9.dist-info")
    sdist = _write_sdist(tmp_path)
    _assert_rejected(capsys, [wheel, sdist])


def test_requires_exact_sdist_pkg_info_regular_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = _write_wheel(tmp_path)
    missing = _write_sdist(tmp_path, include_metadata=False)
    _assert_rejected(capsys, [wheel, missing])

    missing.unlink()
    special = _write_sdist(
        tmp_path,
        overrides={"PKG-INFO": (tarfile.SYMTYPE, b"", "target")},
    )
    _assert_rejected(capsys, [wheel, special])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
def test_malformed_archive_errors_are_one_fixed_secret_safe_line(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
) -> None:
    if target == "wheel":
        wheel = tmp_path / "secret-member-name.whl"
        wheel.write_bytes(b"not a zip file")
        sdist = _write_sdist(tmp_path)
    else:
        wheel = _write_wheel(tmp_path)
        sdist = tmp_path / "secret-member-name.tar.gz"
        sdist.write_bytes(b"not a gzip tar file")
    _assert_rejected(capsys, [wheel, sdist])


def test_encrypted_zip_members_cannot_escape_fixed_cli_boundary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = _write_wheel(tmp_path)
    _mark_zip_encrypted(wheel)
    sdist = _write_sdist(tmp_path)
    _assert_rejected(capsys, [wheel, sdist])


def test_unsupported_zip_compression_is_rejected_by_fixed_cli_boundary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = _write_wheel(tmp_path, compression=zipfile.ZIP_BZIP2)
    sdist = _write_sdist(tmp_path)
    _assert_rejected(capsys, [wheel, sdist])


def test_success_output_sanitizes_controls_and_bounds_basenames(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = _write_wheel(
        tmp_path,
        filename=("w" * 110) + "\nforged.whl",
    )
    sdist = _write_sdist(tmp_path)
    assert VERIFIER.main([str(wheel), str(sdist)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 1
    assert "\nforged" not in captured.out
    wheel_display = captured.out.split("wheel=", maxsplit=1)[1].split(
        " sdist=", maxsplit=1
    )[0]
    assert len(wheel_display) <= 96
    assert all(character.isprintable() for character in wheel_display)


def test_only_the_repo_root_dotenv_is_ignored() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=ROOT,
        input=".env\nnested/.env\n.env.backup\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [".env"]


def test_ci_and_manual_release_gates_are_structurally_offline_and_fail_fast() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    release = (ROOT / "docs/RELEASE.md").read_text()
    release_lower = release.casefold()
    offline_command = 'pytest -q -m "not live"'

    for version in ("'3.11'", "'3.12'", "'3.13'", "'3.14'"):
        assert version in workflow
    assert offline_command in workflow
    assert offline_command in release
    assert "run: pytest -q\n" not in workflow
    assert "set -euo pipefail" in release
    assert "cleanup()" in release
    assert "trap cleanup EXIT" in release
    assert release.index("set -euo pipefail") < release.index("artifact_dir=")
    assert "\npython -m " not in release
    assert "\npython scripts/" not in release
    assert release.index("trap cleanup EXIT") < release.index("python3 -m build")
    for forbidden in (
        "twine upload",
        "publish",
        "actions/upload",
        "attest",
        "id-token: write",
        "contents: write",
        "korail_mobile_api_live",
        "srt_mobile_api_live",
    ):
        assert forbidden not in workflow.casefold()
        assert forbidden not in release_lower
    assert not re.search(r"(?m)^\s*release\s*:", workflow)
    assert not re.search(r"(?m)^\s*tags\s*:", workflow)


def test_ambient_live_opt_in_is_deselected_by_the_release_command() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    release = (ROOT / "docs/RELEASE.md").read_text()
    offline_command = 'pytest -q -m "not live"'
    assert offline_command in workflow and offline_command in release

    environment = os.environ.copy()
    environment[LIVE_ENV] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-m",
            "not live",
            "tests/test_live_service.py",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 5
    assert "1 deselected" in result.stdout

def test_repository_truth_and_full_mutation_policy() -> None:
    readme = (ROOT / "README.md").read_text()
    # docs/NEXT_SESSION.md was consolidated into IMPLEMENTATION_PROGRESS.md; its
    # repository-truth handoff facts now live in that doc's Package Handoff Summary.
    handoff = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text()
    for document in (readme, handoff):
        assert "54 routes" in document
        assert "65 public methods" in document
        assert "2091 passed" in document and "1 deselected" in document
        assert "docs/RELEASE.md" in document
        assert "5 cars" in document
        assert "75 seat rows" in document
        assert "IRG000000" in document
        assert "service-status preflight" in document

    policy = (ROOT / "docs/library-build-guide.md").read_text().casefold()
    forbidden_recommendations = (
        "reservationapi",
        "paymentapi",
        "refundapi",
        "runtime opt-in",
        "dryrun=true",
        "opt-in과 dry-run marker 필요",
        "confirmation token needed",
        "default guarded",
        "default disabled",
    )
    for phrase in forbidden_recommendations:
        assert phrase not in policy
    for requirement in (
        "no flag",
        "no dry-run marker",
        "no confirmation token",
        "separate safety design",
        "new evidence",
        "independent review",
        "explicit user authorization",
    ):
        assert requirement in policy


def test_canonical_plan_requires_behavioral_release_verification() -> None:
    # The dual-package release-readiness plan under docs/superpowers/plans/ was
    # removed during the docs consolidation; its behavioral release-verification
    # contract now lives in docs/RELEASE.md ("Behavioral verification contract").
    plan = (ROOT / "docs/RELEASE.md").read_text().casefold()
    for requirement in (
        "behavioral",
        "duplicate",
        "zero-byte",
        "requires-dist",
        "r:gz",
        "symlink",
        "fixed stderr",
        "set -euo pipefail",
        'pytest -q -m "not live"',
    ):
        assert requirement in plan
    assert "write one failing release contract test per repository" not in plan
    assert "is_file() checks are sufficient" not in plan
