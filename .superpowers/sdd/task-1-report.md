# Task 1 Report: Package Scaffold And Metadata

Implemented the Task 1 package scaffold for the KORAIL Python client.

What changed:
- Added `pyproject.toml` with the requested build metadata, runtime dependencies, test extra, package discovery, and pytest configuration.
- Created `src/korail_mobile_api/__init__.py` with the requested public exports.
- Added `src/korail_mobile_api/config.py`, `errors.py`, `models.py`, and `client.py`.
- Added `tests/test_models.py` with the exact metadata, import, and dataclass assertions from the brief.

Verification:
- Initial red step surfaced an environment issue because `pytest` was not installed on the machine.
- Installed the package in editable mode with test dependencies using `python3 -m pip install -e '.[test]'`.
- Verified the task file with `python3 -m pytest tests/test_models.py -q`.
- Ran the full test suite with `python3 -m pytest -q`.

Result:
- All tests passed: `3 passed`.

Notes:
- Scope stayed limited to scaffold, metadata, exports, and dataclasses.
- No login, HTTP transport, crypto workflow, read APIs, or live smoke behavior was added.
