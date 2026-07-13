# KORAIL Empty Advertising ID Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `txtDeviceId=""` the default ticket-list request while preserving non-empty advertising-ID overrides.

**Architecture:** Resolve the default once in `KorailConfig`, let the live environment builder use an optional override, and make the payload builder serialize the resolved string without truthiness validation. Keep authentication, endpoint safety, ticket fields, and response handling unchanged.

**Tech Stack:** Python 3.11+, dataclasses, httpx form encoding, pytest.

## Global Constraints

- Default `KorailConfig.advertising_id` is exactly `""`.
- `txtDeviceId` is always present in the ticket-list form, including as `txtDeviceId=`.
- A non-empty caller or `KORAIL_ADVERTISING_ID` environment value is preserved unchanged.
- Missing credentials and DynaPath device identity remain preflight errors.
- Do not change DynaPath, cache parsing, reservation/payment, or unrelated endpoints.
- Work inline on `main` as explicitly requested; preserve the existing untracked `dist/` directory.
- Use one RED command and one final full-suite GREEN command; do not add repeated review/build cycles.

---

### Task 1: Default and Serialize Empty Advertising ID

**Files:**
- Modify: `src/korail_mobile_api/config.py:16-30`
- Modify: `src/korail_mobile_api/payloads.py:1-102`
- Modify: `src/korail_mobile_api/live.py:36-70`
- Modify: `tests/test_public_contract.py:76-98`
- Modify: `tests/test_client_read_apis.py:124-153`
- Modify: `tests/test_live.py:32-61`
- Modify: `tests/test_readme.py:7-25`
- Modify: `README.md:125-137`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md:35-82`

**Interfaces:**
- Consumes: `KorailConfig(advertising_id: str)`, `build_ticket_list_form(config, page_no)`, and `build_config_from_env()`.
- Produces: default `advertising_id=""`, optional environment override, and a ticket-list form that always contains `txtDeviceId`.

- [ ] **Step 1: Add failing contract, request, and live-config tests**

Add these assertions/tests while retaining the existing non-empty `ad-id` request test:

```python
def test_config_defaults_advertising_id_to_empty_string():
    assert KorailConfig().advertising_id == ""
```

```python
def test_ticket_list_defaults_to_empty_device_id(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.myTicket.MyTicketList": (
                "ticket_list_empty.json"
            ),
        },
    )
    client.session.current = KorailSession(
        jsessionid="session",
        member_no="member",
    )

    client.get_ticket_list()

    assert "txtDeviceId=" in captured[0]["body"]
```

```python
def test_build_config_from_env_defaults_advertising_id_to_empty(monkeypatch):
    import korail_mobile_api.live as live

    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "device-1")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "14")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S911N")
    monkeypatch.delenv("KORAIL_ADVERTISING_ID", raising=False)

    config = live.build_config_from_env()

    assert config.advertising_id == ""
```

Update the README contract test to require the exact phrase
`KORAIL_ADVERTISING_ID is optional`.

- [ ] **Step 2: Run one focused RED command**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_public_contract.py tests/test_client_read_apis.py tests/test_live.py tests/test_readme.py -q
```

Expected: failures for the `None` config default, the ticket-list preflight
exception, the required live environment variable, and missing optional README
wording. Existing unrelated tests must continue collecting normally.

- [ ] **Step 3: Implement the minimal behavior change**

Change the configuration field to:

```python
advertising_id: str = ""
```

Remove the `KorailProtocolError` import and advertising-ID truthiness guard from
`payloads.py`; retain this field in the returned form:

```python
"txtDeviceId": config.advertising_id,
```

Change the live environment resolution to:

```python
advertising_id = os.environ.get("KORAIL_ADVERTISING_ID", "")
```

Keep the existing non-empty environment test as override coverage.

- [ ] **Step 4: Update current documentation once**

In `README.md`, state `KORAIL_ADVERTISING_ID is optional and defaults to an
empty string`, and show the optional export as:

```bash
export KORAIL_ADVERTISING_ID=""
```

In `docs/IMPLEMENTATION_PROGRESS.md`, record the observed empty-ID live result
`WRT300005`/`SUCC`, remove the claim that advertising ID blocks live preflight,
and identify cache envelope handling as the remaining full-helper blocker.
Update the offline test count only after the final test run, using its actual
result.

- [ ] **Step 5: Run one final GREEN verification and commit**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
git diff --check
```

Expected: zero failures and the existing opt-in live test skip. Update the
progress count to the exact output if needed, run `git diff --check` once more
only if that count changed, then commit the scoped files:

```bash
git add src/korail_mobile_api/config.py src/korail_mobile_api/payloads.py src/korail_mobile_api/live.py tests/test_public_contract.py tests/test_client_read_apis.py tests/test_live.py tests/test_readme.py README.md docs/IMPLEMENTATION_PROGRESS.md docs/superpowers/plans/2026-07-13-korail-empty-advertising-id.md
git commit -m "fix: allow empty korail advertising id"
```

The final status may still show the pre-existing untracked `dist/` directory.
