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

python -m pip install -e ".[test]"
python -m pip install build
PYTHONPATH="$PWD/src" pytest -q -m "not live"

artifact_dir="$(mktemp -d)"
venv_dir="$(mktemp -d)"
outside_dir="$(mktemp -d)"
python -m build --wheel --sdist --outdir "$artifact_dir" .
wheel_path="$(find "$artifact_dir" -maxdepth 1 -name '*.whl' -print -quit)"
sdist_path="$(find "$artifact_dir" -maxdepth 1 -name '*.tar.gz' -print -quit)"
python scripts/verify_distribution.py "$wheel_path" "$sdist_path"
python -m venv "$venv_dir"
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
