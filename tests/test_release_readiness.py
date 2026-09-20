# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

from __future__ import annotations

import os
import re
import subprocess
import sys
import tarfile
import tomllib
import warnings
import zipfile
from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "korail_mobile_api"
PROJECT_NAME = "korail-mobile-api"
LIVE_ENV = "KORAIL_MOBILE_API_LIVE"
CLIENT_NAME = "KorailClient"
EXPECTED_LICENSE_EXPRESSION = "Apache-2.0"
EXPECTED_LICENSE_FILES = ["LICENSE", "NOTICE"]
# The checkout's own bytes, not a stand-in. The verifier compares every licence
# member of both artifacts against these, so a fixture that invented its own
# payload would be testing a licence this repository does not ship.
#
# NOTICE is declared beside LICENSE because Apache-2.0 section 4(d) obliges a
# redistributor to carry the attribution notices forward, and a wheel that
# ships only LICENSE leaves everyone downstream unable to do that. The notice
# here is not decorative: it records which prior-art checkouts were read and
# that no code was taken from them, which is exactly the claim a redistributor
# would need to be able to repeat.
LICENSE_PAYLOADS = {name: (ROOT / name).read_bytes() for name in EXPECTED_LICENSE_FILES}
LICENSE_PAYLOAD = LICENSE_PAYLOADS[EXPECTED_LICENSE_FILES[0]]
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
                dict(LICENSE_PAYLOADS)
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
        **dict(LICENSE_PAYLOADS),
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


def test_installed_package_version_matches_the_built_version() -> None:
    """Nothing in the build keeps these two in step. This test is that thing.

    ``__version__`` is a hand-written literal and ``project.version`` is a
    hand-written literal; a release that bumps one and forgets the other ships
    a package that misreports itself to every caller that asks.
    """
    import korail_mobile_api

    assert korail_mobile_api.__version__ == VERSION
    # Dunders are not exported names.
    assert "__version__" not in korail_mobile_api.__all__

    source = (ROOT / "src" / PACKAGE_NAME / "__init__.py").read_text(encoding="utf-8")
    assert f'__version__ = "{VERSION}"' in source


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


@pytest.mark.parametrize(
    "forged",
    (
        ("w" * 110) + "\nforged.whl",
        "a\rb\x00c\x1bd.whl",
        ("\n" * 200) + ".whl",
    ),
)
def test_bounded_name_strips_controls_and_caps_length(forged: str) -> None:
    """The sanitiser itself, on names no filesystem would hold.

    This used to be reachable only by creating a file whose basename carried
    the control character, which Windows refuses outright -- so the one
    assertion that mattered ran on two platforms out of three. ``_bounded_name``
    takes a ``Path``, not an open file, so the forged name never has to exist.
    """
    display = VERIFIER._bounded_name(Path(forged))

    assert len(display) <= 96
    assert all(character.isprintable() for character in display)
    assert "\n" not in display


def test_success_output_bounds_the_basename_it_prints(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """And the bound survives the trip through ``main``.

    The name here is long but filesystem-legal everywhere, because this case is
    about the printed line -- one line, no stderr, name capped -- and not about
    the character classes, which the parametrisation above covers directly.
    """
    wheel = _write_wheel(tmp_path, filename=("w" * 110) + "forged.whl")
    sdist = _write_sdist(tmp_path)
    assert VERIFIER.main([str(wheel), str(sdist)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 1
    wheel_display = captured.out.split("wheel=", maxsplit=1)[1].split(
        " sdist=", maxsplit=1
    )[0]
    assert len(wheel_display) <= 96
    assert all(character.isprintable() for character in wheel_display)


def _child_pytest(
    *arguments: str,
    environment: dict[str, str],
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """자식 프로세스로 ``pytest`` 를 돌리고 stdout 을 UTF-8 문자열로 받는다.

    ``PYTHONIOENCODING`` 을 세우는 것이 이 함수의 존재 이유다. 파이프에 묶인 자식
    파이썬은 stdout 인코딩을 로케일에서 가져오므로 한국어 Windows 에서는 cp949 로
    쓴다. 지금은 이 스위트의 테스트 이름이 전부 ASCII 라서 우연히 통과하지만,
    한글이 든 이름 하나만 생겨도 ``--collect-only`` 출력이 cp949 바이트가 되고,
    그것을 부모가 UTF-8 로 읽으면 ``subprocess`` 의 읽기 스레드가
    ``UnicodeDecodeError`` 로 죽어 ``result.stdout`` 이 문자열이 아니라 ``None``
    이 된다 (자매 저장소 srt-mobile-api 에서 실제로 그렇게 깨졌다). 자식 쪽
    인코딩을 못박는 것이 부모 쪽에서 ``errors="replace"`` 로 덮는 것보다 낫다 —
    뒤엣것은 깨진 글자를 통과시켜 놓고 고쳐진 척한다.

    ``timeout`` 은 호출자가 정한다. Windows 에서 pytest 의 콜드 스타트가 눈에
    띄게 느려서, 이 값은 "이 하위 프로세스가 멈추지 않았다"만 보장하며 성능을
    재지 않는다.
    """
    return subprocess.run(
        [sys.executable, "-m", "pytest", *arguments],
        cwd=ROOT,
        env={**environment, "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
    )


def test_ambient_live_opt_in_is_deselected_by_the_release_command() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    release = (ROOT / "docs/RELEASE.md").read_text(encoding="utf-8")
    offline_command = 'pytest -q -m "not live"'
    assert offline_command in workflow and offline_command in release

    environment = os.environ.copy()
    environment[LIVE_ENV] = "1"
    result = _child_pytest(
        "-q",
        "-m",
        "not live",
        "tests/test_live_service.py",
        environment=environment,
        timeout=60,
    )
    assert result.returncode == 5
    assert "1 deselected" in result.stdout


def test_canonical_plan_requires_behavioral_release_verification() -> None:
    # The dual-package release-readiness plan under docs/superpowers/plans/ was
    # removed during the docs consolidation; its behavioral release-verification
    # contract now lives in docs/RELEASE.md ("동작 기반 검증 계약"). The document
    # is Korean, so the four prose requirements are pinned in Korean; the four
    # that are identifiers or literal commands stay as the wire spells them.
    plan = (ROOT / "docs/RELEASE.md").read_text(encoding="utf-8").casefold()
    for requirement in (
        "동작 기반",
        "중복된 멤버",
        "0바이트",
        "requires-dist",
        "r:gz",
        "심볼릭 링크",
        "고정된 stderr",
        "set -euo pipefail",
        'pytest -q -m "not live"',
    ):
        assert requirement in plan
    assert "write one failing release contract test per repository" not in plan
    assert "is_file() checks are sufficient" not in plan
