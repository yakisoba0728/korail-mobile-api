# Agent guide

## Working loop

1. Inspect `git status --short --branch` and the task. Preserve existing work and identify the callers, tests and docs the change reaches.
2. Load the relevant references below before editing. Prefer the existing domain helper and fixture over a new abstraction.
3. For bug fixes, reproduce the failure with a synthetic regression at the public boundary, then make the smallest complete fix. Keep refactors and intentional behavior changes distinguishable.
4. Run the applicable checks under **Verification**. Finish with changed files, commands/results, skipped checks and remaining risks. Commit, push, merge or release only when the user requests it.

## References by task

| Task | Read first |
|---|---|
| Usage, installation, released vs. development behavior | [README.md](README.md), [CHANGELOG.md](CHANGELOG.md) (top entry; `3.0.0` is unreleased), [docs/migration-3.0.md](docs/migration-3.0.md) |
| Requests, parsing, raw data, errors, sessions, queues or money | [checks/BEHAVIOR.md](checks/BEHAVIOR.md), [checks/ACCEPTANCE.md](checks/ACCEPTANCE.md) |
| App compatibility, fields, defaults or protected values | [docs/verification-7010.md](docs/verification-7010.md); distinguish static evidence, limited live observations and unknowns |
| Public API or examples | [docs/api/](docs/api/), the matching [docs/guide/](docs/guide/) page, `tests/test_docs.py`, `tests/test_types.py` |
| Live-validation claims | [docs/status.md](docs/status.md) (current state), [docs/records.md](docs/records.md) and `docs/verification-*.md` (dated records, never rewritten); retain the original date, version, inputs and limits |
| Packaging, CI or publishing | [docs/releasing.md](docs/releasing.md), `pyproject.toml`, `MANIFEST.in`, `.github/workflows/ci.yml`, `tests/test_packaging.py` |

Version sources in `src/korail_mobile_api/` are `__init__.py` (package), the request defaults `KORAIL_APP_VERSION`/`KORAIL_API_VERSION` (`constants.py`), and `error_messages.json` (catalog provenance). These versions are independent; `main` can contain Unreleased changes with the same package version as a published release.

## Code map

Runtime paths below are relative to `src/korail_mobile_api/`.

| Change | Entry points |
|---|---|
| Public calls and convenience API | `client.py`, `facade.py`; exports in `__init__.py` (the only public import path) |
| Domain code | `_domains/<domain>/models.py` (responses), `forms.py` (request types and form builders), `parsers.py`; a domain is the `docs/api/` page of the public method using the code: `common` (session), `trains`, `reservations`, `payments`, `tickets` (account), `passes`, `airport_bus`, `checkin` (delivery-checkin) |
| Shared request and parsing rules | `_core/wire.py` (common fields, digit checks), `_core/validation.py`, `_core/parsing.py` |
| HTTP, authentication and cleanup | `_core/http.py`, `_core/session.py`, `_core/crypto.py`, `_core/cleanup.py` |
| Gates, tokens and configuration | `_core/netfunnel.py`, `_core/dynapath.py`, `config.py` (includes device profiles and `build_config_from_env`) |
| Error policy and message catalog | `errors.py` (includes the catalog lookup); catalog generator `checks/build_error_catalog.py` |
| Public enums and aliases | `constants.py` |

The `tests/records/_*_unsupported.py` modules are reference records, not supported APIs; they and the code only they use stay out of the package.

Comment policy: a comment says why in one line; delete restatements, version notes and live-observation counts (those live in `docs/status.md` and the dated records).
App-source pointers (`*.java:N`, `.smali`) go in the docstring of the test that pins the behavior; a protected literal in `src` keeps one `# evidence: app X.Y.Z File:N` line (`tests/test_source_policy.py`).
Docstrings are one Korean summary line, plus a safety sentence when the call changes server state; keep `#:` field docs that render on the docs site.

## Structural consumers

These read files, names or exact text. Update them together with the structure they read.

- `tests/test_docs.py` parses `KorailClient` in `client.py` by AST and needs exactly one ```` ```python ```` signature block per public method in `docs/api/*.md`. Every other ```` ```python ```` block in README and `docs/` must import from the package root and bind to real signatures; fence 2.x "before" code as ```` ```text ````. It runs the blocks marked by `continuation = result.next_page()` (`docs/getting-started.md`) and `include_no_seats=False`, `passengers = KorailPassengerCounts(adult=2, child=1)`, `option=KorailReserveOption.GENERAL_FIRST` (`docs/guide/convenience.md`).
- `.github/workflows/ci.yml` reads the exact `_F8_SOCKET_GUARD` assignment in `tests/conftest.py` by AST, and its installed-wheel job copies a fixed list of test files by name (including `test_wire_equivalence.py` and `_wire_pin.py`); a renamed file silently leaves that run.
- `tests/_wire_pin.py` is a captured oracle: never edit or regenerate it. A method rename changes only the `RENAMED` map in `tests/test_wire_equivalence.py`.
- `tests/test_packaging.py` hardcodes the sdist top-level files, the `checks/` and `tests/` files that must ship, and the record modules in `tests/records/`; it also requires README to equal the wheel's long description, so README uses absolute URLs and keeps the `docs/assets/*` file names.
- `docs/changelog.md` includes `CHANGELOG.md` by snippet, so CHANGELOG links are absolute. Counts such as the number of public methods or error codes are pinned in tests; do not repeat them in guides.

## Safety boundaries

- Work offline by default. Use synthetic identifiers and `httpx.MockTransport` through the existing test fixtures. README examples and `build_config_from_env` are not offline test harnesses.
- Require explicit permission for live requests, login attempts and state changes. The agreed scope must cover each reservation, cancellation, payment or refund; an approval to test or merge code is not transaction permission.
- Keep credentials, cookies, tokens, PNRs, card data and real response bodies out of commits, reports and fixtures. Models and exception `raw` are not automatically masked.
- Preserve queue/token checks and unresolved app values. Record missing evidence rather than inventing protected literals, endpoints or successful compatibility claims.
- Publishing workflows are manual. Use [docs/releasing.md](docs/releasing.md) only for an explicitly requested release; documentation changes or a merge do not authorize deployment.

## Compatibility-sensitive changes

- Preserve public imports, signatures, return types and pickle paths unless the requested change explicitly alters them. Update exports, API signatures, guides and public contract tests together when it does.
- Wire order, repeated fields, blank omission, missing vs. null, exception identity/cause, session cleanup and no-retry behavior are contracts. Read the task-specific rules in `checks/BEHAVIOR.md`; a generic parser or dict comparison is not a substitute.
- A parsing or transport failure after a mutation does not prove that the server rejected it. Preserve the original/partial error data and verify state before any separately authorized retry.
- Refund quote binding and mileage conversion have different purposes. Keep original-ticket/companion checks and the existing ASCII/int32/zero-fallback comparison; do not merge it with stricter money parsers or change Python's global integer-conversion limit.

## Verification

Use the environment setup and full check commands in [docs/releasing.md](docs/releasing.md) (`로컬 검증`). Use an existing verified development environment when available; otherwise create the documented `.venv`. Run commands from the repository root.

- Start with the affected domain's `tests/test_*.py`. `tests/conftest.py` owns socket blocking, synthetic sessions and the `f8_client_factory` / `scripted_client_factory` transports. Keep response counts and cleanup observable.
- Keep independent expected payloads and app-derived evidence. Extend a readable parameter table instead of adding another HTTP harness; do not regenerate expectations from the code being tested.
- For runtime changes, run the full pytest suite, Ruff checks/format, mypy and Pyright before handoff. The full suite includes the two offline checker CLIs and archive-policy tests; checkout tests do not replace CI's isolated installed-wheel checks.
- For README or public-doc changes, run `tests/test_docs.py`, `tests/test_packaging.py` and the strict documentation build. These check Python examples, signatures and the README embedded in distribution metadata. Check new Markdown links and anchors too; `--strict` does not check absolute URLs.

Report actual results with the tested revision and environment. Mark incomplete checks explicitly; offline passes are not evidence of live server acceptance. Avoid permanent test-count or coverage snapshots in this guide.
