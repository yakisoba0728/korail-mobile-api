# Task 2 Report

## Summary
Implemented the HTTP, parsing, redaction, and safety core for the KORAIL Python client package.

## What changed
- Added `KorailHttpClient` with form POST and JSON GET helpers backed by `httpx`.
- Added `parse_base_response()` with protocol validation and app-level failure handling.
- Normalized raw KORAIL envelope parsing so `strResult` maps to `BaseKorailResponse.str_result`.
- Added redaction helpers for sensitive keys and card-like values.
- Added safety domain exclusions and defaults.
- Added test fixtures and focused tests for HTTP, parsing, redaction, and safety behavior.
- Exported the new Task 2 interfaces from the package root.

## Verification
- `pytest tests/test_http.py tests/test_redaction_safety.py -q`
- `pytest -q`

## Commit
- `3b705ee feat: add korail http and safety core`

## Concerns
- None.

## Follow-up Fix
- `KorailHttpClient.post_form()` and `KorailHttpClient.get_json()` now catch JSON decode failures and raise `KorailProtocolError`.
- `BaseKorailResponse.from_raw()` now rejects responses missing `h_msg_cd`, `h_msg_txt`, or `strResult`.
- Added focused coverage for `get_json()` success, malformed/non-JSON responses, and missing-envelope parsing.
- Reused `tests/fixtures/dynapath_403.json` as the malformed-envelope fixture body.

## Test Output
Focused:
```text
10 passed in 0.06s
```

Full:
```text
13 passed in 0.05s
```
