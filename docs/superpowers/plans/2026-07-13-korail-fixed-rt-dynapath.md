# KORAIL Fixed-RT DynaPath Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rolling DynaPath request-delta engine and duplicate probe implementation with one canonical generator that uses SDK version `v1` and emits exactly one `rt=0` field per token.

**Architecture:** Keep `DynapathTokenSettings` as the runtime identity boundary and keep `DynapathTokenGenerator` as the injectable callable used by `KorailHttpClient`, but remove all request history from both. Promote the successful probe contract into `generate_dynapath_token()`, remove probe-only symbols, and leave exact-path header attachment and 403 classification unchanged.

**Tech Stack:** Python 3.11+, dataclasses, httpx, pytest, standard-library random/string/time/url encoding.

## Global Constraints

- Every generated built-in DynaPath payload contains exactly one literal `rt=0` field.
- The canonical defaults are SDK version `v1` and four random characters from uppercase ASCII letters plus digits.
- Keep the raw application-signature setting `[38ff229cb34c7dda8e28220a2d750cce]`; `_java_form_encode()` must encode it exactly once.
- Keep caller-supplied device id, app-start timestamp, OS version, and device model; do not introduce probe identity defaults into live configuration.
- Keep the custom `token_provider`, exact-path allowlist, DynaPath header name, and DynaPath-specific 403 handling unchanged.
- Remove `recent_request_deltas`, the rolling timestamp queue, and all probe-only functions, classes, constants, and package exports.
- Do not add ticket lookup, reservation, payment, NetFunnel, Sid, or unrelated API changes.
- The worktree already contains substantial uncommitted user work in every relevant source and test file. Do not discard it, stage those whole files, or create implementation commits that would silently absorb it. Use scoped diffs and leave the implementation changes unstaged for user review.

---

## File Structure

- `src/korail_mobile_api/dynapath.py`: sole fixed-RT token algorithm, settings, and stateless callable adapter.
- `src/korail_mobile_api/__init__.py`: canonical public exports with probe-only names removed.
- `tests/test_dynapath.py`: deterministic token vector, fixed-RT repetition, HTTP header, and configuration regression tests.
- `tests/test_http.py`: package constant/export contract and unchanged HTTP behavior.
- `tests/test_live.py`: live environment settings use caller identity and SDK version `v1`.
- `tests/test_readme.py`: current documentation describes the fixed-RT engine and no compatibility probe.
- `README.md`: user-facing DynaPath configuration and behavior.
- `docs/IMPLEMENTATION_PROGRESS.md`: current implementation and verification status.

### Task 1: Replace Stateful and Probe Token Generation

**Files:**
- Modify: `tests/test_dynapath.py:1-216`
- Modify: `tests/test_http.py:1-78`
- Modify: `tests/test_live.py:45-58`
- Modify: `src/korail_mobile_api/dynapath.py:1-482`
- Modify: `src/korail_mobile_api/__init__.py:17-113`

**Interfaces:**
- Consumes: `DynapathTokenSettings`, `DynapathConfig`, `generate_dynapath_token(settings, *, timestamp_ms=None, random_text=None)`, and the existing HTTP token-settings hook.
- Produces: `DynapathTokenGenerator(settings, *, timestamp_ms_provider=None, random_text_provider=None)` as a stateless callable returning one canonical token per call; package default `KORAIL_DYNAPATH_SDK_VERSION == "v1"`.

- [ ] **Step 1: Write failing fixed-RT behavior tests**

In `tests/test_dynapath.py`, remove `dataclasses.replace`, `KorailClient`, and `KorailProbeDynapathTokenProvider` imports. Change the SDK default assertion to `v1`, replace the stateful/probe tests with the following tests, and update both HTTP expected-token calls to pass the unchanged settings object:

```python
def test_token_settings_do_not_accept_request_history():
    with pytest.raises(TypeError, match="recent_request_deltas"):
        DynapathTokenSettings(
            device_id="DEVICE-1234",
            as_value="[38ff229cb34c7dda8e28220a2d750cce]",
            app_start_ts="1712345600000",
            os_version="13",
            device_model="SM-S928N",
            recent_request_deltas=(100,),
        )


def test_generate_dynapath_token_matches_successful_fixed_rt_reference():
    settings = DynapathTokenSettings(
        device_id="7f000001-android-probe",
        as_value="[38ff229cb34c7dda8e28220a2d750cce]",
        app_start_ts="1712345600000",
        os_version="13",
        device_model="SM-S928N",
    )

    token = generate_dynapath_token(
        settings,
        timestamp_ms=1712345678901,
        random_text="A1B2",
    )

    assert token == (
        "bEeEPSYj1Dm54Mg4Pv4ff4fGKguKkDK1FdDwFGkG9fwdEuJYJ3EuakG9EfldmgE34vnYDmCRKkYEv"
        "YEvYEqYlMEgddaaDFmY4qdaakERvn4dEvvdJfmnJ5KDR9RwqkPkR43kglDwwk13D5yJ9vYuKk1"
        "qkKaRCjkPDD5YRCyvngduKDJEE33D5RkuKDGPDJEE33D5RD4dduKDJEE33D5RDyyfwgkG4ddCvn3"
        "dPkYPPYPER43RCqYEvYEvYDFdFfJuwRFPRwjRJmRyEJ93YEqvnMdPkYDFEuCJuwRluDwRfwl3PMG"
        "nJRwv3uFdyjJuCEgddaaDFmvngy4Ryln"
    )


def test_dynapath_generator_has_no_cross_request_state():
    timestamps = iter([1712345600100, 1712345600250])
    random_texts = iter(["A1B2", "C3D4"])
    settings = make_settings()
    generator = DynapathTokenGenerator(
        settings,
        timestamp_ms_provider=lambda: next(timestamps),
        random_text_provider=lambda: next(random_texts),
    )

    assert generator() == generate_dynapath_token(
        settings,
        timestamp_ms=1712345600100,
        random_text="A1B2",
    )
    assert generator() == generate_dynapath_token(
        settings,
        timestamp_ms=1712345600250,
        random_text="C3D4",
    )
    assert not hasattr(generator, "recent_request_deltas")
```

Rename `test_http_reuses_one_stateful_generator_across_requests` to `test_http_generates_independent_fixed_rt_tokens_across_requests`, construct `settings = make_settings()`, and use these expectations:

```python
assert captured == [
    generate_dynapath_token(
        settings,
        timestamp_ms=1712345600100,
        random_text="A1B2",
    ),
    generate_dynapath_token(
        settings,
        timestamp_ms=1712345600250,
        random_text="C3D4",
    ),
]
```

Delete `test_stateful_dynapath_generator_keeps_latest_five_deltas` and `test_dynapath_generator_is_per_client_and_survives_logout`; their asserted state no longer exists.

In `tests/test_http.py`, import `korail_mobile_api as api`, remove probe-only imports, import `KORAIL_DYNAPATH_SDK_VERSION`, and replace the probe assertions with:

```python
assert KORAIL_DYNAPATH_SDK_VERSION == "v1"
assert DynapathTokenGenerator
assert not hasattr(api, "KorailProbeDynapathTokenProvider")
assert not hasattr(api, "generate_korail_probe_dynapath_token")
```

In `tests/test_live.py`, replace the old SDK assertion and add the signature assertion:

```python
assert config.dynapath.token_settings.sdk_version == "v1"
assert config.dynapath.token_settings.as_value == (
    "[38ff229cb34c7dda8e28220a2d750cce]"
)
```

- [ ] **Step 2: Run the behavior tests and verify the expected red state**

Run:

```bash
python -m pytest tests/test_dynapath.py tests/test_http.py tests/test_live.py -q
```

Expected: FAIL because settings still accept `recent_request_deltas`, the default SDK version is still `v1.0.3`, the generator still accumulates deltas, and probe-only exports still exist. Fix test syntax or setup errors until failures are only those intended behavior differences.

- [ ] **Step 3: Implement the canonical fixed-RT engine**

In `src/korail_mobile_api/dynapath.py`, remove `replace` from the dataclass import, remove every `KORAIL_PROBE_DYNAPATH_*` constant, and set the canonical defaults exactly as follows:

```python
from dataclasses import dataclass, field

DYNAPATH_RANDOM_ALPHABET = string.ascii_uppercase + string.digits
KORAIL_DYNAPATH_SDK_VERSION = "v1"
```

Remove this field from `DynapathTokenSettings`:

```python
recent_request_deltas: tuple[int, ...] = (0,)
```

Replace the payload field construction in `generate_dynapath_token()` with one fixed field list:

```python
fields = [
    ("ai", settings.app_id),
    ("di", settings.device_id),
    ("as", settings.as_value),
    ("su", str(settings.secure_user).lower()),
    ("dbg", str(settings.debug).lower()),
    ("emu", str(settings.emulator).lower()),
    ("hk", str(settings.hooked).lower()),
    ("it", settings.app_start_ts),
    ("ts", str(ts)),
    ("rt", "0"),
    ("os", settings.os_version),
    ("dm", settings.device_model),
    ("st", settings.os_type),
    ("sv", settings.sdk_version),
]
```

Delete `_probe_random_text()`, `generate_korail_probe_dynapath_token()`, and `KorailProbeDynapathTokenProvider` in full. Replace `DynapathTokenGenerator` with this stateless adapter:

```python
class DynapathTokenGenerator:
    def __init__(
        self,
        settings: DynapathTokenSettings,
        *,
        timestamp_ms_provider: TimestampMsProvider | None = None,
        random_text_provider: RandomTextProvider | None = None,
    ) -> None:
        self.settings = settings
        self._timestamp_ms_provider = timestamp_ms_provider or _timestamp_ms
        self._random_text_provider = random_text_provider or _random_text

    def __call__(self, _context: DynapathRequestContext | None = None) -> str:
        return generate_dynapath_token(
            self.settings,
            timestamp_ms=self._timestamp_ms_provider(),
            random_text=self._random_text_provider(),
        )
```

In `src/korail_mobile_api/__init__.py`, remove these imports and matching `__all__` entries:

```python
KorailProbeDynapathTokenProvider
KORAIL_PROBE_DYNAPATH_AS_VALUE
KORAIL_PROBE_DYNAPATH_DEVICE_ID
KORAIL_PROBE_DYNAPATH_DEVICE_MODEL
KORAIL_PROBE_DYNAPATH_OS_VERSION
KORAIL_PROBE_DYNAPATH_SDK_VERSION
generate_korail_probe_dynapath_token
```

Do not modify `src/korail_mobile_api/http.py` or `src/korail_mobile_api/live.py`; their existing settings-based wiring will use the new stateless adapter and new default constants automatically.

- [ ] **Step 4: Run the focused behavior tests and verify green**

Run:

```bash
python -m pytest tests/test_dynapath.py tests/test_http.py tests/test_live.py -q
```

Expected: all tests in the three files pass with no warnings or import errors.

- [ ] **Step 5: Review the scoped runtime diff without staging user work**

Run:

```bash
git diff -- src/korail_mobile_api/dynapath.py src/korail_mobile_api/__init__.py tests/test_dynapath.py tests/test_http.py tests/test_live.py
git diff --check
```

Expected: the scoped diff contains only the fixed-RT replacement on top of the existing worktree edits; `git diff --check` exits 0. Do not run `git add` for these already-dirty files.

### Task 2: Update Current Documentation Contract

**Files:**
- Modify: `tests/test_readme.py:7-21`
- Modify: `README.md:144-171`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md:27-54`

**Interfaces:**
- Consumes: the fixed-RT public behavior and exports from Task 1.
- Produces: current documentation that names `DynapathTokenSettings`, SDK `v1`, and fixed `rt=0`, with no probe compatibility guidance.

- [ ] **Step 1: Write the failing README contract test**

Replace `test_readme_describes_live_scope_and_probe_provider_consistently` with:

```python
def test_readme_describes_fixed_rt_dynapath_consistently():
    text = README.read_text(encoding="utf-8")
    assert "This work is static analysis only." not in text
    assert "The committed material is documentation" not in text
    assert "caller-supplied" in text
    assert "fixed `rt=0`" in text
    assert "SDK version `v1`" in text
    assert "DynapathTokenSettings" in text
    assert "compatibility-only" not in text
    assert "KorailProbeDynapathTokenProvider" not in text
    assert "KORAIL_DYNAPATH_DEVICE_ID" in text
    assert "KORAIL_ADVERTISING_ID" in text
    assert "get_app_data()" in text
    assert "get_notice()" in text
    assert "/file/CACHE/prdMobilePlusMain.cache" in text
    assert "/file/CACHE/prdMobilePlusNotice.cache" in text
    assert "appDataLoaded" in text
    assert "noticeLoaded" in text
```

- [ ] **Step 2: Run the README test and verify red**

Run:

```bash
python -m pytest tests/test_readme.py -q
```

Expected: FAIL because the README still describes a stateful generator and a compatibility-only probe provider.

- [ ] **Step 3: Replace the obsolete DynaPath documentation**

Replace `README.md:144-171` with:

```markdown
DynaPath is supported for the documented allowlist paths. Runtime constants
such as `Device`, API version, app key, DynaPath header name, and allowlist paths
are importable from the package. Live smoke constructs `DynapathTokenSettings`
only from required caller-supplied environment values and fails before request
construction when any required identity value is missing.

The built-in generator follows the successful fixed `rt=0` contract: SDK
version `v1`, four uppercase-letter-or-digit random characters, and exactly one
`rt=0` field in each token payload. The app-start timestamp is captured once
when live configuration is built; request history is not accumulated. The raw
application-signature setting is form-encoded exactly once during token
construction.

When enabled, the client attaches `DYNAPATH_HEADER_NAME` only for the documented
DynaPath allowlist paths. Callers that need an external implementation may
still provide a custom `DynapathConfig.token_provider`; the package contains no
separate probe generator or rolling-delta mode. Login follows the app sequence
and treats only `IRZ000001` or `S200` as final success.
```

In `docs/IMPLEMENTATION_PROGRESS.md`, replace the current stateful claims with:

```markdown
- Fixed `rt=0` DynaPath generation and exact-path attachment
```

and:

```markdown
- Fixed `rt=0` DynaPath generated tokens for login and train search using the
  successful `v1` token contract; no request-delta state is retained
```

Change “DynaPath non-regression tests” to “fixed-RT DynaPath tests.” Do not rewrite the historical spec/plan files; the new design spec explicitly supersedes their stateful requirements.

- [ ] **Step 4: Run the README contract test and verify green**

Run:

```bash
python -m pytest tests/test_readme.py -q
```

Expected: the README test passes.

- [ ] **Step 5: Review the scoped documentation diff without staging user work**

Run:

```bash
git diff -- README.md tests/test_readme.py docs/IMPLEMENTATION_PROGRESS.md
git diff --check
```

Expected: only current behavior wording changes; historical documents remain untouched; whitespace check exits 0.

### Task 3: Full Verification and Handoff

**Files:**
- Verify: `src/korail_mobile_api/dynapath.py`
- Verify: `src/korail_mobile_api/__init__.py`
- Verify: `tests/test_dynapath.py`
- Verify: `tests/test_http.py`
- Verify: `tests/test_live.py`
- Verify: `tests/test_readme.py`
- Verify: `README.md`
- Verify: `docs/IMPLEMENTATION_PROGRESS.md`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: fresh focused/full test evidence and a scoped unstaged diff suitable for user review.

- [ ] **Step 1: Search for stale runtime and current-documentation references**

Run:

```bash
rg -n "recent_request_deltas|KorailProbeDynapathTokenProvider|generate_korail_probe_dynapath_token|KORAIL_PROBE_DYNAPATH|v1\.0\.3|stateful DynaPath|rolling-delta" src tests README.md docs/IMPLEMENTATION_PROGRESS.md
```

Expected: no matches. Matches in historical `docs/superpowers/specs` and `docs/superpowers/plans` are intentionally excluded from this command.

- [ ] **Step 2: Run focused regression tests**

Run:

```bash
python -m pytest tests/test_dynapath.py tests/test_http.py tests/test_live.py tests/test_readme.py -q
```

Expected: all focused tests pass with zero failures.

- [ ] **Step 3: Run the complete offline test suite**

Run:

```bash
python -m pytest -q
```

Expected: zero failures. The existing opt-in live test may remain skipped when live credentials/flags are absent.

- [ ] **Step 4: Build both package artifacts**

Run:

```bash
python -m build
```

Expected: wheel and source distribution build successfully with exit code 0.

- [ ] **Step 5: Perform final diff and worktree verification**

Run:

```bash
git diff --check
git status --short
git diff -- src/korail_mobile_api/dynapath.py src/korail_mobile_api/__init__.py tests/test_dynapath.py tests/test_http.py tests/test_live.py tests/test_readme.py README.md docs/IMPLEMENTATION_PROGRESS.md
```

Expected: no whitespace errors; the design-spec commit remains separate; all pre-existing unrelated worktree changes remain present; implementation files remain unstaged.

- [ ] **Step 6: Report the handoff without claiming live verification**

Report the exact focused/full test counts, build result, files changed, removal of rolling/probe behavior, and the fact that live network smoke was not run unless the user separately supplied the opt-in environment and requested it. Do not claim server acceptance from offline token-vector tests alone.
