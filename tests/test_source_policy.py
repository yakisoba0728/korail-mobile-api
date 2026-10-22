"""Comment policy for the package source: app-source pointers live only on versioned evidence lines.

Contract evidence belongs in the tests that pin it; src keeps one ``# evidence: app X.Y.Z File:N`` line per protected
literal or wire constant (plans/3.0-spec.md section 2).
"""

from __future__ import annotations

import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "korail_mobile_api"
POINTER = re.compile(r"\.(java|smali|kt)\b")
EVIDENCE = re.compile(r"# evidence: app \d+\.\d+\.\d+ ")


def test_app_source_pointers_only_on_evidence_lines() -> None:
    files = sorted(SRC.rglob("*.py"))
    assert files, SRC
    offenders = [
        f"{path.relative_to(SRC)}:{number}: {line.strip()}"
        for path in files
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if POINTER.search(line) and not EVIDENCE.match(line.lstrip())
    ]
    assert not offenders, "\n".join(offenders)
