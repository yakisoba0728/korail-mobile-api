# Current KORAIL Package Handoff

Last updated: 2026-07-14 KST

## Head and base evidence

The internal release-readiness work is based on
`259553bbb930c51d8bc28d1144baa49d17372e3c`. Compare that base's
`docs/IMPLEMENTATION_PROGRESS.md` with the same file at current `HEAD`: the
release work changes package metadata, artifact checks, CI, and documentation,
but does not change runtime requests, routes, credentials, or live behavior.

The current implementation evidence establishes:

- 27 routes at the exact login/read transport boundary.
- 30 public methods on `KorailClient`.
- A reviewed `0.2.0` offline gate of `733 passed, 1 deselected`; the deselected
  test is the explicitly opted-in live-service test.
- No callable reservation, payment, cancellation, refund, check-in, membership,
  or other mutation route.

## Completed read package

The successful-read expansion is complete. Eleven public read methods were
added with frozen typed models, exact payloads, strict parsing, synthetic
fixtures, and no adjacent or fallback requests. Independent review findings
were corrected before the historical `435 passed, 1 skipped` baseline.

The earlier cache, DynaPath, UUID, generic MAAS menu, and MAAS station phases
are also complete at current `HEAD`. The release-readiness change does not
repeat production traffic and does not alter their established contracts.

The `0.2.0` typed seat-inventory increment adds two authenticated,
DynaPath-disabled reads with closed general-room forms, strict frozen response
models, and pre-Sid validation. Its offline contract and sanitized four-step
evidence helper are implemented. The sole authorized attempt was spent: it
stopped at setup with `status=setup_failed`, operation calls `0/0/0/0`, and
`sufficiency=insufficient_setup`, so it produced no live endpoint evidence. It
must not be retried under this task. Any future attempt requires
separate explicit authorization.

Use [docs/RELEASE.md](RELEASE.md) for the internal-only offline test, build,
distribution verifier, fresh-wheel install, and cleanup gate.

## Historical analysis map

The static APK inventory remains historical evidence rather than a statement
that every discovered endpoint is implemented. Its committed entry points are:

- [README.md](../README.md)
- [docs/korail-apk-analysis.md](korail-apk-analysis.md)
- [docs/api-endpoints.md](api-endpoints.md)
- [docs/deep-dive/README.md](deep-dive/README.md)
- [docs/deep-dive/api-contracts.md](deep-dive/api-contracts.md)
- [docs/deep-dive/network-model-fields.md](deep-dive/network-model-fields.md)

The original APK and generated `analysis/` trees remain ignored local
artifacts. They are not inputs to the internal release gate.

## Next candidates

1. Internal release preparation is completed by this handoff; rerun
   [docs/RELEASE.md](RELEASE.md) whenever package contents change.
2. Do not retry the spent seat-inventory live gate under this task. Any future
   attempt requires separate explicit authorization and must remain outside the
   broad live smoke.
3. Any new KORAIL read requires separate sanitized evidence, a concrete design,
   offline contract tests, and an independent safety review.
4. Mutation endpoints remain excluded unless a separate safety design and
   explicit authorization establish a new scope.
5. A public release remains blocked by the four items listed in
   [docs/RELEASE.md](RELEASE.md).

Do not run live KORAIL requests as part of release verification. Do not load or
inspect local credentials, APKs, caches, generated analysis, or raw production
data.
