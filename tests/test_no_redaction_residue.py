"""Nothing tracked in this repository may carry a vendor key or a local path.

The git history of this repository and of its sibling was rewritten so that the
KORAIL and SR apps' third-party credentials -- Google/Firebase API keys, Kakao
and Facebook app keys -- were replaced by ``<...-REDACTED>`` placeholders
everywhere they had been quoted. Those keys are not ours, are not used by either
client, and are not needed to read any document here; only the *field name and
its location in the APK* are.

That rewrite was a one-off pass over the files that existed on the day it ran,
and a one-off pass is exactly the kind of thing that misses a line. It did: a
sentence deep in the srt repository's ``cross-validation-2026-07-21.md`` compared
"the two Google API keys" by quoting a truncated prefix of each, in a spelling
the pass did not look for. It survived because nothing in either suite was
looking either -- the check was a command somebody remembered to run, not a gate.

So this file is the gate, and it is byte-identical in both repositories. It
derives everything it scans from ``git ls-files``, so a document added tomorrow
is covered without anybody adding it here, and it accepts the redaction
placeholders of both apps so that neither repository needs its own copy.

The patterns below are assembled from fragments on purpose. Written as plain
literals, this file would match itself and the test could only pass by excluding
its own source -- which is precisely the kind of hole that lets a real key sit
in an excluded file forever. Split like this, the scanner is scanned too.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

#: The fixed prefix every Google API key starts with, and nothing more.
#: Requiring a body length was the first version of this pattern and it was
#: wrong: the residue that motivated this file was a prefix plus FOUR characters
#: trailing into an ellipsis, which a ``{10,}`` quantifier walks straight past.
#: A pattern for a secret has to match the part of it that gets quoted -- nobody
#: leaks a whole key, they leak just enough of one to identify which they meant.
#: The prefix carries no information on its own, so matching it alone costs
#: nothing: the redacted spellings both repositories use name the key in words
#: and never reproduce it.
#:
#: This comment does not spell the prefix out, and the sample in
#: ``test_the_scanner_would_notice`` builds it by concatenation, for the reason
#: the module docstring gives: a scanner that matches itself has to be excluded
#: from its own scan, and an excluded file is where a real key survives. That is
#: not hypothetical -- an earlier draft of this very line quoted the residue
#: verbatim, and the scan went red on itself the moment the file was committed
#: and became visible to ``git ls-files``.
VENDOR_KEY = re.compile("AIza" + r"Sy")

#: A Firebase realtime-database URL with a real project id in it. Documents are
#: free to describe the *shape*: ``https://<project id>.firebaseio.com`` and
#: ``https://<SRT-APP-FIREBASE-PROJECT-REDACTED>.firebaseio.com`` both contain
#: ``<``, which no project id can, so both are allowed through.
FIREBASE_DATABASE_URL = re.compile(r"https://[A-Za-z0-9_-]+\.firebase" + r"io\.com")

#: An absolute path into somebody's home directory. These leak the machine a
#: document was written on and break for every reader; a repository-relative
#: path is what a reader can actually follow.
HOME_PATH = re.compile("/Us" + r"ers/[A-Za-z0-9._-]+/")

PATTERNS = (
    ("vendor API key", VENDOR_KEY),
    ("Firebase database URL with a project id", FIREBASE_DATABASE_URL),
    ("absolute home-directory path", HOME_PATH),
)


def _tracked_text_files() -> list[Path]:
    """Every file git tracks that decodes as UTF-8.

    ``git ls-files`` rather than a filesystem walk: an untracked scratch file is
    not published and is not this gate's business, while a tracked file is
    exactly what a reader of the repository gets. Files that do not decode are
    skipped, so a binary added later cannot fail this for the wrong reason --
    and neither repository tracks one today.
    """
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    names = [name for name in result.stdout.decode().split("\0") if name]
    assert names, "git ls-files returned nothing; is this a checkout?"
    return [ROOT / name for name in names]


@pytest.mark.parametrize("label,pattern", PATTERNS, ids=[label for label, _ in PATTERNS])
def test_no_tracked_file_carries(label: str, pattern: re.Pattern[str]) -> None:
    offenders: list[str] = []
    for path in _tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert not offenders, f"{label} found in: {offenders}"


def test_the_scanner_would_notice() -> None:
    """A gate that cannot fail is not a gate.

    Each pattern is shown a string it must reject, and every redaction spelling
    the two repositories actually use, which it must accept. Without the first
    half, deleting a character from any regex above would leave the suite green
    and the check dead; without the second, the gate would force the documents
    to stop naming the field at all, which is the information they exist to
    carry.
    """
    # The vendor-key sample is the exact shape that got through: a prefix and
    # four characters, trailing off into an ellipsis. It is not a usable key and
    # was never meant to be -- which is precisely why a length-based pattern
    # missed it and why this one does not.
    rejected = {
        "vendor API key": "AIza" + "SyA2Qx...",
        "Firebase database URL with a project id": (
            "https://some-real-project.firebase" + "io.com"
        ),
        "absolute home-directory path": "/Us" + "ers/somebody/Documents/GitHub/x.md",
    }
    for label, pattern in PATTERNS:
        assert pattern.search(rejected[label]), label

    allowed = (
        "google_api_key = <SRT-APP-GOOGLE-API-KEY-REDACTED>",
        "google_api_key = <KORAIL-APP-GOOGLE-API-KEY-REDACTED>",
        "https://<SRT-APP-FIREBASE-PROJECT-REDACTED>.firebase" + "io.com",
        "https://<KORAIL-APP-FIREBASE-PROJECT-REDACTED>.firebase" + "io.com",
        "https://<project id>.firebase" + "io.com",
        "see docs/analysis/cross-validation-2026-07-21.md",
    )
    for _, pattern in PATTERNS:
        for value in allowed:
            assert pattern.search(value) is None, value
