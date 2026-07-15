# Current KORAIL Package Handoff

Last updated: 2026-07-15 KST

## Head and base evidence

The internal release-readiness work is based on
`259553bbb930c51d8bc28d1144baa49d17372e3c`. Compare that base's
`docs/IMPLEMENTATION_PROGRESS.md` with the same file at current `HEAD`: the
release work changes package metadata, artifact checks, CI, and documentation,
but does not change runtime requests, routes, credentials, or live behavior.

The current implementation evidence establishes:

- 27 routes at the exact login/read transport boundary.
- 30 public methods on `KorailClient`.
- A reviewed `0.2.0` offline gate of `866 passed, 1 deselected`; the deselected
  test is the explicitly opted-in live-service test.
- No callable reservation, payment, cancellation, refund, check-in, membership,
  or other mutation route.

## Completed read package

The successful-read expansion is complete. Eleven public read methods were
added with frozen typed models, exact payloads, strict parsing, synthetic
fixtures, and no adjacent or fallback requests. Independent review findings
were corrected before the historical `435 passed, 1 skipped` baseline. A
bounded 2026-07-15 replay parsed five methods, stopped four at
`KorailProtocolError`, and skipped product detail plus ticket receipt because
no owned identifiers were returned. Later sanitized evidence resolved the
cart, delay-discount, and product-reservation result-only success shapes. Pass
availability remains the only unresolved live parser shape and must not be
guessed from the fixed status-only summary.

The earlier cache, DynaPath, UUID, generic MAAS menu, and MAAS station phases
are also complete at current `HEAD`. The release-readiness change does not
repeat production traffic and does not alter their established contracts.

The `0.2.0` typed seat-inventory increment adds two authenticated,
DynaPath-disabled reads with closed general-room forms, strict frozen response
models, and pre-Sid validation. Its offline contract and sanitized four-step
evidence helper are implemented. A bounded structural run received
`IRG000000`/`SUCC` from both routes with 5 cars and 75 seat rows, while
retaining no raw values or identifiers. That run proved that floor may be
absent, windows may be empty, and repeated seat labels are valid; the parser
now preserves every row. A later post-fix confirmation stopped at the
service-status preflight before login transport and therefore made no search,
car-list, or seat-list call. The final combined run later logged in and again
returned 5 cars and 75 seat rows, with zero windows.

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
2. Do not bypass the service-status preflight. A future bounded confirmation,
   if separately authorized while the service is available, must remain
   outside the broad live smoke.
3. Before changing pass-date parsing, capture only a separately reviewed
   sanitized field/type shape; the current evidence contains an exception class
   but no response structure for that remaining endpoint.
4. Any new KORAIL read requires separate sanitized evidence, a concrete design,
   offline contract tests, and an independent safety review.
5. Mutation endpoints remain excluded unless a separate safety design and
   explicit authorization establish a new scope.
6. A public release remains blocked by the four items listed in
   [docs/RELEASE.md](RELEASE.md).

Do not run live KORAIL requests as part of release verification. Do not load or
inspect local credentials, APKs, caches, generated analysis, or raw production
data.
