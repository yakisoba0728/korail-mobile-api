# Internal development records

This directory is not user documentation. It is the working history of how
this package was analyzed, audited, and brought to its current state:
release-planning notes, adversarial re-verification passes, cross-validation
against a reference implementation, and design specs written before each
feature landed.

Nothing here is a claim about the package as it exists today. Where a document
below disagrees with the current README, CHANGELOG, or source, the current
package is correct — these are dated snapshots of reasoning, not living
documentation. Several of them explicitly record claims that were later
withdrawn or superseded; that history is kept rather than deleted because it
is how a later reader can tell a closed question from an open one.

These files moved out of `docs/` on 2026-07-27, when the package first became
a public release, so that a reader looking for "how do I use this" is not
routed through internal audit trails. The move only changed location, not
content: citations inside these documents still use their pre-move paths
(for example `docs/RELEASE_GAP_PLAN.md` or `docs/deep-dive/impl-audit-*.md`)
and were not rewritten. If you are trying to resolve one of those citations
today, drop the `docs/` prefix and look under `docs/internal/` — most of what
moved is here.

## What is here

- `RELEASE_GAP_PLAN.md` — the working plan that tracked every mutation gap
  between this client and the app, closed one at a time.
- `deep-dive/impl-audit-2026-07-22.md` and its five `impl-audit-reverify*`
  passes — successive adversarial re-verifications of the same divergence
  claims, most of which did not survive re-checking.
- `deep-dive/cross-validation-2026-07-21.md` — reconciliation against the
  `srtgo` reference implementation's behavior.
- `audit-2026-07-27/` — a four-phase, multi-agent audit (per-service findings,
  cross-check, and independent verification passes).
- `superpowers/specs/` — the design spec written before each feature was
  implemented.

For the package as it is today, start at the repository root
[README.md](../../README.md) instead.
