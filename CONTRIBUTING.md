# Contributing

## Workflow

1. Fork and branch from `main`.
2. Make your change. If it touches documentation, expect a test to check it —
   see "Documentation is measured, not asserted" below before you write a
   number or a claim by hand.
3. Run the offline gate before opening a pull request:

   ```bash
   pip install -e ".[test]"
   env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"
   ```

   This must pass with no network access. It is the only gate; there is no
   separate lint or type-check step to run locally beyond what the test suite
   already exercises.
4. Do not run the live-service tests (`-m live` / `KORAIL_MOBILE_API_LIVE=1`)
   as part of a contribution. They require a real account and make real
   requests against `smart.letskorail.com`; that is the maintainer's call to
   make against their own account, not something a contribution should
   trigger. See "Reporting a bug" below for what evidence to include instead.
5. Open a pull request. **Before you do, read the checklist in
   `.github/pull_request_template.md` about not pasting credentials, PNRs, or
   real server responses** — it applies to the PR description and to every
   diff, fixture, and screenshot in it.

## Documentation is measured, not asserted

This repository has repeatedly caught documentation drifting out of sync with
the code it describes — route counts, method names, and test counts have each
been wrong in the README at some point because they were hand-maintained
literals nobody re-derived when the code moved on. `tests/test_readme.py` and
`tests/test_release_readiness.py` exist to catch that class of drift by
deriving the expected value from the code (`korail_mobile_api.__all__`,
`safety.KORAIL_READ_ONLY_ROUTES`, `inspect.getmembers(KorailClient, ...)`,
and similar) and asserting the document states that derived value — not by
freezing a number in the test itself.

If your change adds or removes a public name, a route, or a mutation method,
expect an existing test to fail until you update the prose that names it. If
you add a new hand-maintained count anywhere (a document or a test), prefer
deriving it from the code instead; a second hand-kept copy of a number is how
this repository's drift happened the first three times.

## Changes to the mutation consent / safety model

This package ships a small, consent-gated mutation surface (see
`docs/MUTATION_HANDOFF.md` and `SECURITY.md`) on top of a much larger
read-only one. Every mutation method is denied by default, gated by category,
route-owner-checked, and form-shape-checked before anything leaves the
process — see `src/korail_mobile_api/consent.py` and `safety.py` for the
mechanism, and `docs/library-build-guide.md` ("Suggested Library Modules" /
mutation policy) for the standard this was held to when it was authorized.

A pull request that touches any of the following is held to that same
standard, not a lower one for being "just a fix":

- adding a new mutation route or category to the allowlist in `safety.py`,
- widening what `require_mutation_consent`, `post_mutation_form`, or
  `get_mutation_query` accept,
- changing a default (`dry_run`, `fake_card_only`,
  `real_card_acknowledged`, or any per-category `allow_*` flag) toward
  permissive,
- changing what `redact_payload` treats as sensitive.

Concretely, that means:

- **Cite your evidence by file:line, not by assertion.** A claim about what
  the app sends needs a decompiled-APK citation (`ClassName.java:NN`, or the
  equivalent smali) or a specific bounded live-evidence run — the same
  citation discipline the rest of this repository's audits use. "I believe
  the app does X" is not evidence; "`TCReservationDao.java:23-40` builds this
  FieldMap" is.
- **Do not paste decompiled source.** Point at `file:line` and describe it in
  your own words; quote wire names only (route paths, `@Field`/`@Query` keys,
  literal constant values) in short backtick spans. This repository does not
  reproduce the app's own source text, and a PR that does will need to be
  rewritten before it can be merged.
- **A new mutation capability needs review, not just tests passing.** The
  four-part bar this project used for every mutation category it has shipped
  is unchanged: a separate safety design, new evidence, independent review,
  and explicit user authorization. A green test suite demonstrates the code
  does what you built it to do; it does not by itself demonstrate that the
  thing you built should be allowed to exist. Open an issue describing the
  capability and its evidence before sending a large diff — it is much
  cheaper to agree on the safety design before the code exists than after.
- **No new hand-maintained list.** If your change needs to be reflected in a
  count or a name list somewhere, make that list (or count) derive from
  `safety.py` / `consent.MUTATION_CATEGORIES` / the client class the way the
  existing tests do, rather than adding a document that repeats it by hand.

## Reporting a bug

Open an issue using the bug report template
(`.github/ISSUE_TEMPLATE/`). Prefer a decompiled-APK citation
(`file:line`) or a minimal, sanitized reproduction over pasted real output —
see the template for what not to include.

For a security-relevant issue (anything that could cause an unintended state
change, an unapproved charge, or credential/PII exposure), use
[GitHub Security Advisories](https://github.com/yakisoba0728/korail-mobile-api/security/advisories/new)
instead of a public issue; see `SECURITY.md`.
