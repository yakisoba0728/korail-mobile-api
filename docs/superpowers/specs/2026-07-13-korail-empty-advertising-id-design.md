# KORAIL Empty Advertising ID Design

**Status:** Implemented and bounded-live-verified on 2026-07-13

## Context

The ticket-list client currently requires a non-empty `advertising_id` before
constructing a request. Live verification showed that the KORAIL
`MyTicketList` endpoint accepts the normal member form with
`txtDeviceId=""` and returns a successful application response. The client-side
precondition is therefore stricter than the observed server contract and
prevents the standard live helper from running when no advertising ID is
available.

## Decision

Treat an empty advertising ID as the normal default while preserving an
explicit caller or environment override.

- `KorailConfig.advertising_id` defaults to the empty string.
- `build_config_from_env()` reads `KORAIL_ADVERTISING_ID` as optional and uses
  the empty string when the variable is missing or empty.
- `build_ticket_list_form()` always includes `txtDeviceId`, even when its value
  is empty.
- A supplied non-empty advertising ID remains unchanged and is sent as-is.

Alternatives considered and rejected:

- Hard-coding an empty value would ignore valid caller-provided device
  identity.
- Omitting `txtDeviceId` when empty would not match the live-verified request
  shape.
- Retaining the current validation would preserve a restriction disproved by
  the bounded live request.

## Data Flow and Error Handling

`KorailConfig` owns the resolved advertising-ID string. The live environment
builder passes `os.environ.get("KORAIL_ADVERTISING_ID", "")` into that field.
The ticket-list payload builder serializes the field without truthiness
validation, so form encoding produces `txtDeviceId=` for the default.

Authentication and all other ticket-list fields remain unchanged. Missing
credentials and DynaPath device identity still fail during live preflight.
Transport, protocol, authentication, and application-response errors retain
their current classifications.

## Testing

Implementation will follow a red-green cycle:

1. Prove `KorailConfig()` defaults `advertising_id` to `""`.
2. Prove ticket-list request construction sends `txtDeviceId=` with the
   default configuration.
3. Preserve the existing test that a supplied `ad-id` is sent unchanged.
4. Prove live environment configuration succeeds when
   `KORAIL_ADVERTISING_ID` is absent and resolves it to `""`.
5. Prove a non-empty environment override is retained.
6. Run focused payload/client/live tests and the complete offline suite.

The opt-in live smoke remains a separate network check. Tests and logs must not
contain credentials, session identifiers, generated DynaPath tokens, or ticket
response bodies.

## Scope

In scope are configuration defaults, live environment resolution, ticket-list
payload construction, their direct tests, and current README/live-setup wording
if it still marks the advertising ID as required. Reservation, payment,
DynaPath generation, cache-envelope handling, and unrelated endpoints are out
of scope.
