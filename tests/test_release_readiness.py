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
EXPECTED_VERSION = "1.0.0"
EXPECTED_LICENSE_EXPRESSION = "Apache-2.0"
EXPECTED_LICENSE_FILES = ["LICENSE"]
# The checkout's own bytes, not a stand-in. The verifier compares every licence
# member of both artifacts against these, so a fixture that invented its own
# payload would be testing a licence this repository does not ship.
LICENSE_PAYLOAD = (ROOT / EXPECTED_LICENSE_FILES[0]).read_bytes()
EXPECTED_AUTHOR_NAME = "yakisoba0728"
EXPECTED_AUTHOR_EMAIL = "yakihyuk0728@gmail.com"
EXPECTED_AUTHOR_HEADER = f"{EXPECTED_AUTHOR_NAME} <{EXPECTED_AUTHOR_EMAIL}>"
CANONICAL_REPOSITORY = f"https://github.com/yakisoba0728/{PROJECT_NAME}"
EXPECTED_PROJECT_URLS = {
    "Homepage": CANONICAL_REPOSITORY,
    "Repository": CANONICAL_REPOSITORY,
    "Issues": f"{CANONICAL_REPOSITORY}/issues",
    "Changelog": f"{CANONICAL_REPOSITORY}/blob/main/CHANGELOG.md",
}
EXPECTED_PROJECT_URL_HEADERS = [
    f"{label}, {url}" for label, url in EXPECTED_PROJECT_URLS.items()
]
EXPECTED_CLASSIFIERS = {
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Typing :: Typed",
}
# Only the headers a PEP 639 build never emits stay forbidden. The four it does
# emit — License-Expression, License-File, Author-email, Project-URL — moved out
# of this tuple and into exact-value assertions, because dropping them from the
# ban list without checking their contents would leave the owner and licence
# metadata entirely unverified.
FORBIDDEN_METADATA_HEADERS = (
    "License",
    "Author",
    "Maintainer",
    "Maintainer-email",
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


SINGLETON_HEADERS = (
    "Name",
    "Version",
    "Requires-Python",
    "License-Expression",
    "Author-email",
)


def _metadata(
    *,
    singletons: dict[str, list[str]] | None = None,
    classifiers: list[str] | None = None,
    dependencies: list[str] | None = None,
    project_urls: list[str] | None = None,
    license_files: list[str] | None = None,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> bytes:
    singleton_values = {
        "Name": [PROJECT_NAME],
        "Version": [VERSION],
        "Requires-Python": [REQUIRES_PYTHON],
        "License-Expression": [EXPECTED_LICENSE_EXPRESSION],
        "Author-email": [EXPECTED_AUTHOR_HEADER],
    }
    if singletons:
        singleton_values.update(singletons)

    lines = ["Metadata-Version: 2.4"]
    for header in SINGLETON_HEADERS:
        lines.extend(f"{header}: {value}" for value in singleton_values[header])
    lines.extend(
        f"Classifier: {value}"
        for value in (
            sorted(EXPECTED_CLASSIFIERS) if classifiers is None else classifiers
        )
    )
    lines.extend(
        f"Project-URL: {value}"
        for value in (
            EXPECTED_PROJECT_URL_HEADERS if project_urls is None else project_urls
        )
    )
    lines.extend(
        f"License-File: {value}"
        for value in (EXPECTED_LICENSE_FILES if license_files is None else license_files)
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
    license_members: dict[str, bytes] | None = None,
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
            members = (
                {name: LICENSE_PAYLOAD for name in EXPECTED_LICENSE_FILES}
                if license_members is None
                else license_members
            )
            for name, payload in members.items():
                archive.writestr(f"{dist_info}/licenses/{name}", payload)
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
        **{name: LICENSE_PAYLOAD for name in EXPECTED_LICENSE_FILES},
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
    assert PROJECT["version"] == EXPECTED_VERSION
    assert PROJECT["requires-python"] == ">=3.11"
    assert PROJECT["keywords"] == EXPECTED_KEYWORDS
    assert set(PROJECT["classifiers"]) == EXPECTED_CLASSIFIERS
    assert len(PROJECT["classifiers"]) == len(EXPECTED_CLASSIFIERS)
    assert "maintainers" not in PROJECT

    # PEP 639 SPDX form, not the deprecated table, and not a duplicate claim in
    # the classifier list — the two are mutually exclusive.
    assert PROJECT["license"] == EXPECTED_LICENSE_EXPRESSION
    assert PROJECT["license-files"] == EXPECTED_LICENSE_FILES
    assert not [
        value for value in PROJECT["classifiers"] if value.startswith("License ::")
    ]
    assert PROJECT["authors"] == [
        {"name": EXPECTED_AUTHOR_NAME, "email": EXPECTED_AUTHOR_EMAIL}
    ]
    assert PROJECT["urls"] == EXPECTED_PROJECT_URLS

    build_requires = CONFIGURATION["build-system"]["requires"]
    # `license-files` is silently ignored before setuptools 77, which would
    # produce a wheel with no licence file and a build that still succeeds.
    assert "setuptools>=77" in build_requires

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert CONFIGURATION["tool"]["setuptools"]["package-data"][PACKAGE_NAME] == [
        "py.typed"
    ]

    marker = ROOT / "src" / PACKAGE_NAME / "py.typed"
    assert marker.is_file()
    assert marker.read_bytes() == b""
    for relative_path in (
        "MANIFEST.in",
        "LICENSE",
        "CHANGELOG.md",
        "SECURITY.md",
        "docs/RELEASE.md",
        "scripts/verify_distribution.py",
        ".github/workflows/ci.yml",
    ):
        assert (ROOT / relative_path).is_file()


def test_installed_package_version_matches_the_built_version() -> None:
    """Nothing in the build keeps these two in step. This test is that thing.

    ``__version__`` is a hand-written literal and ``project.version`` is a
    hand-written literal; a release that bumps one and forgets the other ships
    a package that misreports itself to every caller that asks.
    """
    import korail_mobile_api

    assert korail_mobile_api.__version__ == VERSION
    assert korail_mobile_api.__version__ == EXPECTED_VERSION
    # Dunders are not exported names.
    assert "__version__" not in korail_mobile_api.__all__

    source = (ROOT / "src" / PACKAGE_NAME / "__init__.py").read_text(encoding="utf-8")
    assert f'__version__ = "{EXPECTED_VERSION}"' in source


@pytest.mark.parametrize(
    ("project", "reason"),
    (
        ({"license": {"text": "Apache-2.0"}}, "deprecated license table"),
        ({"license": {"file": "LICENSE"}}, "deprecated license file table"),
        ({"license": ""}, "empty expression"),
        ({}, "no licence declared at all"),
    ),
)
def test_license_expression_must_be_the_spdx_string_form(
    project: dict[str, object],
    reason: str,
) -> None:
    with pytest.raises(VERIFIER.ContractError):
        VERIFIER._license_expression(project, list(EXPECTED_CLASSIFIERS))


def test_license_expression_rejects_a_duplicate_classifier_claim() -> None:
    """PEP 639 makes `License ::` classifiers mutually exclusive with SPDX."""
    with pytest.raises(VERIFIER.ContractError):
        VERIFIER._license_expression(
            {"license": EXPECTED_LICENSE_EXPRESSION},
            [*EXPECTED_CLASSIFIERS, "License :: OSI Approved :: Apache Software License"],
        )
    assert (
        VERIFIER._license_expression(
            {"license": EXPECTED_LICENSE_EXPRESSION},
            list(EXPECTED_CLASSIFIERS),
        )
        == EXPECTED_LICENSE_EXPRESSION
    )


@pytest.mark.parametrize(
    "value",
    (
        None,
        [],
        ["LICEN[CS]E*"],
        ["LICENSE*"],
        ["LICENSE?"],
        ["LICENSE", "LICENSE"],
        [""],
        ["/LICENSE"],
        [b"LICENSE"],
        "LICENSE",
    ),
)
def test_license_files_must_be_unique_literal_paths(value: object) -> None:
    project = {} if value is None else {"license-files": value}
    with pytest.raises(VERIFIER.ContractError):
        VERIFIER._license_files(ROOT, project)


@pytest.mark.parametrize("problem", ("absent", "empty", "directory"))
def test_license_files_must_name_readable_non_empty_files_in_the_checkout(
    tmp_path: Path,
    problem: str,
) -> None:
    """The declared path is resolved against the checkout, not merely parsed.

    The bytes read here are what both artifacts are later compared against, so
    a declaration naming a file that does not exist — or one that exists and is
    blank — would make the comparison vacuous: an empty licence in the checkout
    would be copied into both archives and match itself.
    """
    if problem == "empty":
        (tmp_path / "LICENSE").write_bytes(b"  \n\t\n")
    elif problem == "directory":
        (tmp_path / "LICENSE").mkdir()
    with pytest.raises(VERIFIER.ContractError):
        VERIFIER._license_files(tmp_path, {"license-files": EXPECTED_LICENSE_FILES})


def test_license_files_carries_the_checkouts_own_bytes() -> None:
    """The positive that makes the negatives above mean something."""
    declared = VERIFIER._license_files(ROOT, {"license-files": EXPECTED_LICENSE_FILES})
    assert declared == (
        (EXPECTED_LICENSE_FILES[0], (ROOT / EXPECTED_LICENSE_FILES[0]).read_bytes()),
    )
    assert b"Apache License" in declared[0][1]


@pytest.mark.parametrize(
    "value",
    (
        None,
        [],
        [{"name": "a", "email": "a@example.com"}, {"name": "b", "email": "b@example.com"}],
        [{"name": "yakisoba0728"}],
        [{"email": "yakihyuk0728@gmail.com"}],
        [{"name": "", "email": "a@example.com"}],
        [{"name": "a", "email": ""}],
        [{"name": "a <b>", "email": "a@example.com"}],
        [{"name": "a, b", "email": "a@example.com"}],
        [{"name": "a", "email": "a@example.com, b@example.com"}],
        [{"name": " a ", "email": "a@example.com"}],
        [{"name": "a", "email": "a@example.com", "extra": "x"}],
    ),
)
def test_author_email_requires_exactly_one_unambiguous_owner(value: object) -> None:
    project = {} if value is None else {"authors": value}
    with pytest.raises(VERIFIER.ContractError):
        VERIFIER._author_email(project)


@pytest.mark.parametrize(
    "value",
    (
        None,
        {},
        {"Homepage": "http://github.com/yakisoba0728/korail-mobile-api"},
        {"Home, page": CANONICAL_REPOSITORY},
        {"Homepage": ""},
        {"Homepage": f" {CANONICAL_REPOSITORY}"},
        {"Homepage": 1},
    ),
)
def test_project_urls_must_be_labelled_https_entries(value: object) -> None:
    project = {} if value is None else {"urls": value}
    with pytest.raises(VERIFIER.ContractError):
        VERIFIER._project_urls(project)


def test_the_repository_pyproject_satisfies_every_new_contract_rule() -> None:
    """The negatives above are only meaningful if the positive still holds."""
    contract = VERIFIER._project_contract()
    assert contract.version == EXPECTED_VERSION
    assert contract.license_expression == EXPECTED_LICENSE_EXPRESSION
    assert contract.license_files == (
        (EXPECTED_LICENSE_FILES[0], (ROOT / EXPECTED_LICENSE_FILES[0]).read_bytes()),
    )
    assert contract.author_email == EXPECTED_AUTHOR_HEADER
    assert set(contract.project_urls) == set(EXPECTED_PROJECT_URL_HEADERS)
    assert len(contract.project_urls) == len(EXPECTED_PROJECT_URL_HEADERS)


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
        # A build that quietly relicensed, or one that named a different owner,
        # is the whole reason these two stopped being merely forbidden.
        ("License-Expression", EXPECTED_LICENSE_EXPRESSION, "MIT"),
        ("Author-email", EXPECTED_AUTHOR_HEADER, "someone <someone@example.com>"),
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
@pytest.mark.parametrize("problem", ("missing", "extra", "duplicate", "wrong-url"))
def test_requires_the_exact_canonical_project_url_set(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    problem: str,
) -> None:
    """A URL set that is close but not equal points users somewhere else.

    The failure this catches is not a typo, it is a redirect: an ``Issues``
    entry aimed at a repository the owner does not control still looks like
    plausible metadata to everyone reading it.
    """
    project_urls = list(EXPECTED_PROJECT_URL_HEADERS)
    if problem == "missing":
        project_urls.remove(f"Issues, {EXPECTED_PROJECT_URLS['Issues']}")
    elif problem == "extra":
        project_urls.append("Funding, https://example.invalid/sponsor")
    elif problem == "duplicate":
        project_urls.append(project_urls[0])
    else:
        project_urls[0] = "Homepage, https://github.com/someone-else/korail-mobile-api"
    wheel, sdist = _pair_with_metadata(
        tmp_path,
        target,
        _metadata(project_urls=project_urls),
    )
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("target", ("wheel", "sdist"))
@pytest.mark.parametrize("problem", ("missing", "extra", "wrong"))
def test_requires_the_exact_declared_license_file_headers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    problem: str,
) -> None:
    if problem == "missing":
        license_files: list[str] = []
    elif problem == "extra":
        license_files = [*EXPECTED_LICENSE_FILES, "NOTICE"]
    else:
        license_files = ["COPYING"]
    wheel, sdist = _pair_with_metadata(
        tmp_path,
        target,
        _metadata(license_files=license_files),
    )
    _assert_rejected(capsys, [wheel, sdist])


#: A licence that is present, non-empty, and not the one this project ships.
#: ``.strip()``-style presence checks accept it; only a byte comparison against
#: the checkout rejects it, which is the difference this constant exists to
#: exercise.
ALTERED_LICENSE_PAYLOAD = LICENSE_PAYLOAD.replace(
    b"Apache License", b"Someone Else License", 1
)


@pytest.mark.parametrize("problem", ("missing", "empty", "altered", "truncated", "misplaced"))
def test_wheel_must_carry_the_declared_license_text_not_only_a_header(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    problem: str,
) -> None:
    """``License-Expression: Apache-2.0`` is a claim; the file is the licence.

    Without this gate a wheel whose METADATA advertises Apache-2.0 while
    carrying no licence text at all passes verification, and the installed
    ``dist-info`` gives the user nothing to read. ``altered`` and ``truncated``
    are the cases a presence-only check waves through: both are non-empty files
    at the right path that are not the licence this repository ships.
    """
    if problem == "missing":
        license_members: dict[str, bytes] = {}
    elif problem == "empty":
        license_members = {"LICENSE": b"   \n"}
    elif problem == "altered":
        license_members = {"LICENSE": ALTERED_LICENSE_PAYLOAD}
    elif problem == "truncated":
        license_members = {"LICENSE": LICENSE_PAYLOAD[:64]}
    else:
        license_members = {"../LICENSE": LICENSE_PAYLOAD}
    wheel = _write_wheel(tmp_path, license_members=license_members)
    sdist = _write_sdist(tmp_path)
    _assert_rejected(capsys, [wheel, sdist])


@pytest.mark.parametrize("problem", ("missing", "empty", "altered", "truncated", "symlink"))
def test_sdist_must_carry_the_declared_license_text_as_a_regular_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    problem: str,
) -> None:
    wheel = _write_wheel(tmp_path)
    if problem == "missing":
        sdist = _write_sdist(tmp_path, missing=("LICENSE",))
    elif problem == "symlink":
        sdist = _write_sdist(
            tmp_path,
            overrides={"LICENSE": (tarfile.SYMTYPE, b"", "../LICENSE")},
        )
    else:
        payload = {
            "empty": b"\n\n",
            "altered": ALTERED_LICENSE_PAYLOAD,
            "truncated": LICENSE_PAYLOAD[:64],
        }[problem]
        sdist = _write_sdist(
            tmp_path,
            overrides={"LICENSE": (tarfile.REGTYPE, payload, "")},
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


_COLLECTED_RE = re.compile(
    r"(?m)^(?:(?P<selected>\d+)/(?P<total>\d+)|(?P<only>\d+)) tests? collected"
    r"(?: \((?P<deselected>\d+) deselected\))?"
)


def _collected_offline_test_count() -> tuple[int, int]:
    """How many tests ``-m "not live"`` actually selects, and how many it drops.

    Collection rather than a run: it is the same selection the documents
    describe, it costs a fraction of a second, and a suite that RUNS itself to
    check its own count would double every future test's cost.

    The environment is scrubbed of the live opt-in on purpose. Neighbouring
    tests set it deliberately, and a count that quietly depended on an ambient
    variable would be no better than the hardcoded string this replaced.
    """
    environment = os.environ.copy()
    environment.pop(LIVE_ENV, None)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-m", "not live", "--collect-only"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:]
    match = _COLLECTED_RE.search(result.stdout)
    assert match is not None, result.stdout[-2000:]
    selected = int(match.group("selected") or match.group("only"))
    return selected, int(match.group("deselected") or 0)


def test_repository_truth_and_full_mutation_policy() -> None:
    readme = (ROOT / "README.md").read_text()
    # docs/NEXT_SESSION.md was consolidated into IMPLEMENTATION_PROGRESS.md; its
    # repository-truth handoff facts now live in that doc's Package Handoff Summary.
    handoff = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text()
    # The README was rewritten on 2026-07-26 for people who want to use the
    # library; its audit log moved whole to docs/verification-record.md. The
    # repository-truth numbers a reader needs in order to decide whether to
    # trust the package stayed in the README, and the bounded seat-inventory
    # evidence that supports one of them followed the prose into the record.
    record = (ROOT / "docs/verification-record.md").read_text()
    for document in (readme, handoff):
        assert "60 routes" in document
        # 76, not 72 or 74. Older numbers appear in the handoff, because those
        # sentences were true when written and are kept as history; the pin has
        # to name the CURRENT boundary or it stops detecting the next drift.
        assert "77 public methods" in document
        assert "docs/RELEASE.md" in document

    # The offline gate figure is DERIVED, not pinned. It used to be the literal
    # string "2398 passed, 1 deselected" written out in four places across three
    # documents and asserted in two test modules -- seven hand-kept copies of one
    # number, which is how the sibling srt repository's README came to advertise
    # 1607 tests for a suite that ran 1662. Adding a single test invalidated all
    # seven at once. Asking the suite for its own count means a stale document
    # fails here on its own, and the fix is to correct the document rather than
    # to chase the assertion.
    #
    # Only the CURRENT gate is derived. The 1246/1247 figures elsewhere in these
    # documents are labelled history: they were true on the day they were
    # written, can never change, and are pinned literally in tests/test_readme.py
    # for exactly that reason.
    collected, deselected = _collected_offline_test_count()
    current_gate = f"`{collected} passed, {deselected} deselected`"
    for document in (readme, handoff, record):
        assert current_gate in document
    for document in (record, handoff):
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
