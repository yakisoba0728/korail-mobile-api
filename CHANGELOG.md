# Changelog

## Unreleased

- Added four static-only, typed P0 train reads for free-seat car guidance,
  guide-seat conditions, seat-assignment schedules, and merged-seat inquiry.
- Added frozen closed request objects, exact POST field allowlists, strict
  response parsers, repr-hidden identifiers/free text/raw mappings, and
  synthetic-only fixtures without adding a live call or DynaPath route.
- Kept the Java Retrofit names as documentation aliases only and deliberately
  omitted `TrainSummary` convenience chaining and every adjacent mutation.
- Tightened only these four route parsers to require exact `strResult=SUCC`
  after preserving the existing `FAIL`, `P058`, and `WRC000288` errors.
- Added typed session-unverified pass-menu, commuter-kind-menu, and
  crew-request option reads with caller-required runtime discriminator codes;
  any live verification starts only after login.
- Registered only the three statically evidenced exact read contracts; the
  separate state-changing crew-call route remains excluded.
- Added frozen repr-safe models, strict parsers, synthetic fixtures, and
  offline route, request, error, export, and documentation coverage.
- Added three static-evidenced limousine schedule and seat-inventory reads with
  closed caller-supplied query dataclasses, exact POST allowlists, typed
  repr-safe parsers, one-shot session/error handling, and DynaPath disabled.
- Added no live service/menu/train/car constants, seat selection, hold,
  reservation, payment, cancellation, or other mutation capability; the new
  contracts are covered by synthetic fixtures only.
- Reject limousine query subclasses and invoke each concrete dataclass
  validator non-virtually before Sid generation or transport.

## 0.2.0 - 2026-07-14

- Added the static R20 pass-schedule candidate read with a closed
  caller-supplied request, exact DynaPath-disabled form, strict `SUCC` parser,
  and frozen repr-safe nested train models. A conservative login gate remains
  while the server session requirement is unverified; reservation and payment
  calls stay excluded.
- Added authenticated typed car-list and physical-seat inventory reads for the
  fixed main-menu/general-room contract.
- Registered only the two exact read-only POST forms, with validation before
  Sid generation or transport and DynaPath disabled on both routes.
- Added frozen repr-safe response models, strict synthetic-fixture parsers, and
  a separately opted-in bounded evidence command that persists sanitized
  statuses, call counts, bounded counts, and type-presence booleans only.
- Accepted live-evidenced missing floor values, empty window collections, and
  repeated seat labels, plus statically evidenced empty car containers and
  strict numeric strings, while preserving response order.

## 0.1.0 - 2026-07-14

- Prepared the existing installable, typed, read-only KORAIL mobile API client
  for reproducible internal builds and offline verification.
- Retained the 25-route safety boundary and its 28 public client methods;
  mutation operations remain excluded.
