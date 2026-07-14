# Dual Package Internal Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing KORAIL and SRT `0.1.0` packages reproducibly testable, typed, artifact-audited, and documentation-accurate for internal distribution without publishing them or inventing legal/owner metadata.

**Architecture:** Treat both repositories as one coordinated release-readiness bundle while preserving separate commits and package artifacts. Apply the same behavioral release contract to each package: adversarial wheel/sdist fixtures, canonical archive and metadata validation, a fixed CLI error boundary, structurally offline gates, fail-fast cleanup, typed markers, and accurate repository policy. Presence-only checks supplement this contract but cannot satisfy it. Existing API, route, live-helper, authentication, DynaPath, NetFunnel, and safety code remains unchanged.

**Tech Stack:** Python 3.11+, setuptools, `tomllib`, `zipfile`, `tarfile`, pytest, GitHub Actions.

## Global Constraints

- Work only in `/Users/yakisoba/Documents/GitHub/korail-mobile-api/.worktrees/release-readiness` and `/Users/yakisoba/Documents/GitHub/srt-mobile-api/.worktrees/release-readiness`.
- Keep both project versions exactly `0.1.0` and `requires-python = ">=3.11"`.
- This is internal release preparation, not public publishing. Do not create a LICENSE, author/maintainer identity, project URL, remote, tag, release, upload command, or PyPI publication.
- State clearly that public distribution is blocked until the owner chooses a license, owner metadata, canonical repository URL, and explicitly authorizes publication.
- Do not add dependencies to either runtime dependency list.
- Do not change public API methods, routes, payloads, parsers, live helpers, authentication, DynaPath, NetFunnel, retry behavior, credentials, or local environment files.
- Do not make live KORAIL/SRT calls or inspect ignored credentials, APKs, caches, raw responses, cookies, PNRs, tokens, or device identifiers.
- Preserve the exact KORAIL `25 routes / 28 public methods / 435 passed, 1 skipped` and SRT `20 routes / 285 passed, 1 skipped` historical runtime/package boundaries unless fresh offline tests add only release-contract tests.
- Add no reservation, payment, refund, cancellation, check-in, member/point mutation, `act_19`, ATA/ARD, callback, native bridge, or external seat-map code or documentation promise.
- Use one implementation agent for the full bundle and one final whole-bundle reviewer. Do not split by repository or file family.

---

### Task 1: Prepare both packages for reproducible internal release

**Files in each repository:**
- Create in KORAIL: `src/korail_mobile_api/py.typed`
- Create in SRT: `src/srt_mobile_api/py.typed`
- Create: `MANIFEST.in`
- Create: `CHANGELOG.md`
- Create: `SECURITY.md`
- Create: `docs/RELEASE.md`
- Create: `scripts/verify_distribution.py`
- Create: `.github/workflows/ci.yml`
- Create: `tests/test_release_readiness.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`

**KORAIL-only documentation:**
- Modify: `docs/NEXT_SESSION.md`
- Modify: `docs/library-build-guide.md`
- Modify implemented design status lines under `docs/superpowers/specs/` only when `docs/IMPLEMENTATION_PROGRESS.md` proves the design is complete.
- Add this plan file to the KORAIL release-readiness commit.

**SRT-only documentation:**
- Modify: `docs/analysis/srt-app-api-library-spec-2026-07-09.md`
- Modify implemented design status lines under `docs/superpowers/specs/` only when `docs/IMPLEMENTATION_PROGRESS.md` proves the design is complete.

**Interfaces:**
- Produces CLI: `python scripts/verify_distribution.py dist/*.whl dist/*.tar.gz`
- Produces typed-package markers: `korail_mobile_api/py.typed` and `srt_mobile_api/py.typed`, each included in its wheel and sdist.
- Produces offline CI matrix for quoted Python versions `3.11`, `3.12`, `3.13`, and `3.14` plus one package job.
- Does not produce a publishing/upload interface.

- [ ] **Step 1: Write split behavioral release verification suites**

Create `tests/test_release_readiness.py` using only the standard library and
pytest. Build meaningful temporary wheel and sdist fixtures and exercise the
verifier through `main()`. The behavioral matrix must cover canonical member
paths, normalized duplicate names, forbidden backup variants, ZIP symlink and
special-file modes, encrypted/unsupported ZIP members, TAR links/devices/FIFOs
and special forms, strict gzip `r:gz`, one exact sdist root, exact regular paths,
and zero-byte typed markers.

Generate valid and mutated metadata for both archives. Require singleton exact
Name, Version, and Requires-Python values, the exact classifier set without
duplicates, normalized runtime Requires-Dist equality with `pyproject.toml`,
forbidden owner/license/URL header rejection, the exact versioned dist-info
path, and validated sdist PKG-INFO. Prove malformed or unsupported input yields
one fixed stderr line, while success basenames are sanitized and bounded.

Add structural tests for `pytest -q -m "not live"` in CI and release docs, an
ambient live-env regression proving the live test is deselected, `set -euo
pipefail` plus EXIT cleanup, and the complete mutation-policy boundary. Then
load `pyproject.toml` with `tomllib` and retain these source-contract assertions:

```python
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
```

For each repository assert:

```text
project.version == "0.1.0"
project.requires-python == ">=3.11"
EXPECTED_CLASSIFIERS equals project.classifiers as a duplicate-free set
project.license is absent
project.authors is absent
project.maintainers is absent
project.urls is absent
tool.setuptools.package-data.korail_mobile_api == ["py.typed"] in KORAIL
tool.setuptools.package-data.srt_mobile_api == ["py.typed"] in SRT
src/korail_mobile_api/py.typed exists in KORAIL
src/srt_mobile_api/py.typed exists in SRT
MANIFEST.in, CHANGELOG.md, SECURITY.md, docs/RELEASE.md,
scripts/verify_distribution.py, and .github/workflows/ci.yml exist
```

Read the workflow text and assert quoted `3.11`, `3.12`, `3.13`, `3.14`, the
exact `pytest -q -m "not live"` selection, `python -m build`,
`verify_distribution.py`, and a fresh-venv wheel import are present. Read
`docs/RELEASE.md` and assert it identifies the workflow as internal-only, names
the four public-release blockers (license, owner metadata, canonical URL,
explicit authorization), forbids live tests during the release gate, uses
fail-fast cleanup, and contains no `twine upload` or publish command.

Add repository-specific truth assertions:

```text
KORAIL README and docs/NEXT_SESSION.md state 25 routes, 28 public methods,
435 passed / 1 skipped, and link docs/RELEASE.md.
KORAIL library-build-guide no longer recommends public mutation DTO/method stubs.
SRT README describes an installable read-only package rather than only an
"analysis workspace", states 20 routes and 285 passed / 1 skipped, and links
docs/RELEASE.md.
SRT section 12 accurately says the repository retains package source, tests,
progress/spec/plan documents, README, and smoke tooling.
```

- [ ] **Step 2: Run both focused tests and verify RED**

Run in each worktree:

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_release_readiness.py
```

Expected: adversarial fixtures fail across canonical path/type, exact metadata,
CLI-boundary, offline-gate, cleanup, and mutation-policy categories. Fix only
fixture/import setup errors until those behavioral failures are proven.

- [ ] **Step 3: Add exact typed-package and metadata contracts**

In each `pyproject.toml`, keep the existing name, version, description, readme, Python floor, dependencies, and test extra. Add the exact classifier set from Step 1. Use KORAIL keywords `["korail", "read-only", "mobile-api"]` and SRT keywords `["srt", "read-only", "mobile-api"]`. Add the matching exact block:

```toml
[tool.setuptools.package-data]
korail_mobile_api = ["py.typed"]

# In the SRT repository use this key instead:
[tool.setuptools.package-data]
srt_mobile_api = ["py.typed"]
```

Create the empty PEP 561 markers `src/korail_mobile_api/py.typed` and `src/srt_mobile_api/py.typed` in their respective repositories. Create `MANIFEST.in` in each repository that includes `README.md`, `CHANGELOG.md`, `SECURITY.md`, `docs/RELEASE.md`, and that repository's package `py.typed` marker. Do not add license/owner/URL fields.

- [ ] **Step 4: Add the artifact verifier and CI workflow**

Create `scripts/verify_distribution.py` with a command-line `main()` that accepts exactly one wheel and one sdist in any argument order. It must:

```text
read the full expected artifact contract from pyproject.toml
reject missing, duplicate, or unexpected artifact types
inspect wheel ZIP and gzip sdist TAR with r:gz without extracting them
apply the canonical path, duplicate, forbidden-family/backup, ZIP type and
compression, TAR type/root, exact regular-file, and zero-byte rules from Step 1
validate both wheel METADATA and sdist PKG-INFO using exact singleton fields,
the exact classifier set, normalized runtime Requires-Dist, and forbidden headers
require only the exact versioned dist-info/METADATA location
catch every ordinary archive/parser exception at the CLI boundary and print one
fixed stderr line; never print a path, traceback, archive member, or exception
print only allowlisted, bounded artifact basenames in the success summary
```

The GitHub Actions workflow must use read-only contents permission, run
`pytest -q -m "not live"` on Python `3.11` through `3.14`, build wheel/sdist once
on `3.14`, invoke the verifier, install the wheel into a fresh venv, change
outside the checkout, and import the package/client from `site-packages`. It must
not define live environment variables, publish permissions, attestations,
release triggers, tags, or upload steps.

- [ ] **Step 5: Add internal release and security documentation**

For each repository:

```text
CHANGELOG.md: one 0.1.0 entry summarizing the existing read-only package.
SECURITY.md: require private reporting through the owner's existing private
channel; forbid public disclosure of credentials, cookies, tokens, PNRs,
raw responses, or production identifiers; state that mutation endpoints are excluded.
docs/RELEASE.md: exact internal test/build/verifier/fresh-install commands,
set -euo pipefail, an EXIT cleanup trap installed before build, cleanup on both
success and failure, version policy, no-live rule, and explicit public blockers.
README.md: lead with the installable read-only Python package, retain the
analysis/evidence map, link the release/security/changelog documents, and
show editable internal installation without implying PyPI availability.
```

Use `0.y.z` version guidance: patch for compatible fixes, minor for new backward-compatible read APIs, and major for breaking public contracts. Do not claim semantic-version stability before `1.0.0`.

- [ ] **Step 6: Correct repository-specific documentation truth**

KORAIL:

```text
Rewrite docs/NEXT_SESSION.md as a current package handoff using head/base
evidence, 25 routes, 28 public methods, 435 passed / 1 skipped, the completed
successful-read expansion, and the next candidates (internal release completed;
new KORAIL reads require separate evidence). Preserve the static-analysis map
as historical evidence, not the current implementation state.
Remove mutation module/method/DTO execution recommendations from the library
guide. Retain endpoint facts only as historical, non-implementable evidence and
state that no flag, no dry-run marker, and no confirmation token authorizes
mutation. Any future interface requires separate safety design, new evidence,
independent review, and explicit user authorization.
Mark only completed designs as implemented/verified; do not edit speculative
or superseded design content beyond its status line.
```

SRT:

```text
Replace the root analysis-only description with the current installable
read-only package state while retaining APK evidence context.
Correct spec section 12 so its retained-file description matches the current
source/tests/docs/specs/plans/progress/smoke repository. Remove reservation and
payment execution/module recommendations while retaining endpoint observations
as historical, non-implementable evidence under the same no-flag/no-token rule.
Mark only completed selector, mutual, and seat-page designs as
implemented/verified; do not mark pagination or physical-seat schemas complete.
```

- [ ] **Step 7: Run focused GREEN and actual distribution gates**

Run both focused tests and confirm they pass. Then, independently in each worktree:

```bash
PYTHONPATH="$PWD/src" pytest -q -m "not live"
artifact_dir="$(mktemp -d)"
venv_dir="$(mktemp -d)"
python -m build --wheel --sdist --outdir "$artifact_dir" .
wheel_path="$(find "$artifact_dir" -maxdepth 1 -name '*.whl' -print -quit)"
sdist_path="$(find "$artifact_dir" -maxdepth 1 -name '*.tar.gz' -print -quit)"
python scripts/verify_distribution.py "$wheel_path" "$sdist_path"
python -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install "$wheel_path"
```

Change to a temporary directory, unset `PYTHONPATH`, import the package and its
client, and assert the import path contains `site-packages` and not either source
worktree. Run `git diff --check`. The shell transcript must start with `set -euo
pipefail` and install an EXIT cleanup trap before building. Remove all temporary
paths and generated `build/`, `dist/`, and `*.egg-info` directories. Do not invoke
live helpers.

- [ ] **Step 8: Commit once per repository and report**

Commit all intended KORAIL changes as:

```bash
git commit -m "chore: prepare korail internal release workflow"
```

Commit all intended SRT changes as:

```bash
git commit -m "chore: prepare srt internal release workflow"
```

Leave both tracked worktrees clean. Record exact RED/GREEN/full-suite/build/verifier/import outputs, commits, files, and concerns in the ignored combined implementation report. The controller performs one independent whole-bundle review after both commits.
