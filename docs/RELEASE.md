# Internal Release Gate

This is an internal-only build and verification workflow. It does not authorize
a public release or any production-service request.

## Preconditions

- Start from a clean tracked worktree.
- Use Python 3.11 or newer and install the test and build tools locally.
- Live tests are forbidden during this release gate. Do not load credentials,
  local live configuration, cookies, tokens, or production response data.

## Test, build, and verify

Run from the repository root:

```bash
set -euo pipefail

artifact_dir=""
venv_dir=""
outside_dir=""
checkout="$PWD"

cleanup() {
  cd "$checkout" 2>/dev/null || true
  if [[ -n "$artifact_dir" ]]; then rm -rf "$artifact_dir"; fi
  if [[ -n "$venv_dir" ]]; then rm -rf "$venv_dir"; fi
  if [[ -n "$outside_dir" ]]; then rm -rf "$outside_dir"; fi
  rm -rf "$checkout/build" "$checkout/dist"
  find "$checkout" -type d -name '*.egg-info' -prune -exec rm -rf {} +
}
trap cleanup EXIT

python3 -m pip install -e ".[test]"
python3 -m pip install build
PYTHONPATH="$PWD/src" pytest -q -m "not live"

artifact_dir="$(mktemp -d)"
venv_dir="$(mktemp -d)"
outside_dir="$(mktemp -d)"
python3 -m build --wheel --sdist --outdir "$artifact_dir" .
wheel_path="$(find "$artifact_dir" -maxdepth 1 -name '*.whl' -print -quit)"
sdist_path="$(find "$artifact_dir" -maxdepth 1 -name '*.tar.gz' -print -quit)"
python3 scripts/verify_distribution.py "$wheel_path" "$sdist_path"
python3 -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install "$wheel_path"

checkout="$PWD"
cd "$outside_dir"
unset PYTHONPATH
"$venv_dir/bin/python" - <<PY
from pathlib import Path
import korail_mobile_api
from korail_mobile_api import KorailClient

package_path = Path(korail_mobile_api.__file__).resolve()
assert "site-packages" in package_path.parts
assert Path("$checkout").resolve() not in package_path.parents
print(KorailClient.__name__, package_path)
PY
cd "$checkout"
cleanup
trap - EXIT
```

The verifier must receive exactly one wheel and one source distribution. The
fresh import must resolve from `site-packages`, outside the checkout.

## Cleanup

The `EXIT` trap removes temporary directories and local build metadata on both
success and failure. The explicit final cleanup disarms that trap only after all
checks pass.

Finish with `git status --short` and `git diff --check`.

## Version policy

Before `1.0.0`, use `0.y.z`: increment the patch component for compatible
fixes, the minor component for new backward-compatible read APIs, and the major
component for breaking public contracts. The project does not claim semantic
version stability before `1.0.0`.

## Public-release blockers

Every public release remains blocked until all four items exist and are
reviewed: a license, owner metadata, a canonical URL, and explicit authorization.
Internal verification does not satisfy any of these blockers.

## Behavioral verification contract

The distribution verifier (`scripts/verify_distribution.py`) and its offline
suite (`tests/test_release_readiness.py`) enforce a behavioral contract, not a
presence check. Building meaningful wheel and sdist fixtures, the suite drives
the verifier's `main()` and asserts real archive and metadata rejection rather
than confirming that files merely exist. Presence-only checks cannot satisfy
this contract, and each rule below is exercised by a dedicated adversarial
fixture.

The behavioral matrix covers:

- Canonical member paths and normalized duplicate names, so a wheel or sdist
  that carries a duplicate member is rejected.
- Zero-byte `py.typed` markers: the marker must be a regular, empty file in both
  archives; a missing, non-empty, or special-type marker is rejected.
- Exact metadata: singleton `Name`, `Version`, and `Requires-Python`; the exact
  classifier set without duplicates; normalized runtime `Requires-Dist` equality
  with `pyproject.toml`; and rejection of forbidden owner, license, or URL
  headers.
- Archive form: the sdist is inspected as a strict gzip tar (`r:gz`) without
  extraction, and any symlink, hard link, device, FIFO, or other special member
  in either archive is rejected.
- A fixed stderr line on any malformed or unsupported input, never leaking a
  path, traceback, archive member, or exception text.

The gate itself runs `set -euo pipefail` with an `EXIT` cleanup trap and the
offline `pytest -q -m "not live"` selection defined above.
