# Changelog

## 0.2.0 - 2026-07-14

- Added authenticated typed car-list and physical-seat inventory reads for the
  fixed main-menu/general-room contract.
- Registered only the two exact read-only POST forms, with validation before
  Sid generation or transport and DynaPath disabled on both routes.
- Added frozen repr-safe response models, strict synthetic-fixture parsers, and
  a separately opted-in bounded evidence command that persists sanitized
  statuses, call counts, bounded counts, and type-presence booleans only.

## 0.1.0 - 2026-07-14

- Prepared the existing installable, typed, read-only KORAIL mobile API client
  for reproducible internal builds and offline verification.
- Retained the 25-route safety boundary and its 28 public client methods;
  mutation operations remain excluded.
