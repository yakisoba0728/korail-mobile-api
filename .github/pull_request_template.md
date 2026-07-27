<!--
Before you open this: do not paste credentials, tokens, cookies, PNRs
(reservation numbers), ticket numbers, phone numbers, real names, or raw
production server responses anywhere in this PR — not in the description, not
in a commit message, not in a diff, not in a fixture, not in a screenshot.
This client talks to a real ticketing service; anything committed here
becomes public and stays in the git history even if you edit the PR
description afterward. Sanitize before you paste: replace real values, keep
only the field names and structure needed to make your point.
-->

## What this changes and why

## Evidence

<!--
For a behavioral claim (the app sends X / the app does Y), cite a
decompiled-APK file:line or a specific bounded live-evidence run, the way the
rest of this repository's audits do. Quote wire names (route paths,
`@Field`/`@Query` keys, literal constants) in short backtick spans only — do
not paste decompiled source (no ```java/smali/kotlin/xml fences of app code).
-->

## Checklist

- [ ] `pip install -e ".[test]"` then
      `env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"` passes
- [ ] I did not run the live-service tests as part of this change
- [ ] Any new or changed public name, route, or mutation method is reflected
      in the documentation the existing tests check (they will fail and tell
      you where if not)
- [ ] If this touches the mutation consent / safety model (`safety.py`,
      `consent.py`, `redact_payload`, or any default toward permissive), I
      read "Changes to the mutation consent / safety model" in
      CONTRIBUTING.md and cited evidence accordingly
- [ ] No hand-maintained count or list was added; anything countable is
      derived from the code the way the existing tests do
- [ ] I did not paste credentials, PNRs, real names, phone numbers, or raw
      production responses anywhere in this PR
