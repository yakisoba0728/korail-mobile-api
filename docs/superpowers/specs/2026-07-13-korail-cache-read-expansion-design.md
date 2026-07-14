# KORAIL Cache Read Expansion Design

**Date:** 2026-07-13

**Status:** Implemented and bounded-live-verified on 2026-07-13

## Goal

Add the two previously live-evidenced, account-neutral KORAIL cache reads for
app-main data and notice data without expanding into account, ticket,
reservation, payment, or other stateful domains.

## Context

The current public API stabilization working tree is intentionally uncommitted.
Its fresh offline baseline is `146 passed, 1 skipped`, with the skipped test
being the explicitly opted-in live service test. The package currently permits
10 exact login/read routes and owns one stateful DynaPath generator per HTTP
client.

The APK and live analysis record these successful cache contracts:

- `GET /file/CACHE/prdMobilePlusMain.cache`
- `GET /file/CACHE/prdMobilePlusNotice.cache`
- both send only the `timeStamp` query parameter;
- both use the canonical `https://smart.letskorail.com` origin;
- neither requires an authenticated account or ticket state.

The existing `GET /file/CACHE/MobileService.cache` service check provides the
closest transport pattern, but the two new operations return specialized
response fields.

## Scope

### In scope

- Two exact cache routes.
- Two explicit `KorailClient` methods.
- Typed frozen response models for known APK fields.
- Exact timestamp query construction.
- Strict JSON/application-response classification.
- Offline fixtures and MockTransport tests.
- Public exports and public-contract updates.
- Bounded, read-only live-smoke metadata.

### Out of scope

- UUID, product, reservation-history, cart, receipt, delay, pass, coupon, or
  MAAS APIs.
- Reservation, payment, cancellation, refund, check-in, member mutation, or
  point/mileage mutation.
- DynaPath changes or token generation for the cache routes.
- Automatic persistence or logging of raw cache responses.
- A permissive text fallback for malformed or non-JSON responses.

## Public API

`KorailClient` gains:

```python
def get_app_data(
    self,
    timestamp_ms: int | None = None,
) -> AppDataResponse: ...

def get_notice(
    self,
    timestamp_ms: int | None = None,
) -> NoticeResponse: ...
```

When `timestamp_ms` is `None`, the request uses the current Unix epoch in
milliseconds. An explicitly supplied timestamp makes tests and caller-driven
cache validation deterministic. Validation requires
`type(timestamp_ms) is int and timestamp_ms >= 0`; booleans, negative values,
and other types are rejected before I/O.

The operations are account-neutral. They do not inspect
`KorailSessionClient.current`, add member fields, or require login.

## Models

Add these frozen dataclasses:

```python
@dataclass(frozen=True)
class AppVersionInfo:
    message: str | None = None
    new_version: str | None = None


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    disability_certification_msg: str | None = None
    for_seat_intg: str | None = None
    airport_bus_msg: str | None = None
    railplus_cardinfo: str | None = None
    version: AppVersionInfo | None = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    board_id: str | None = None
    post_sequence: str | None = None
    post_title: str | None = None
```

The parser maps protocol fields exactly:

- `version.AMESSAGE` -> `AppVersionInfo.message`
- `version.NEWDVERSION` -> `AppVersionInfo.new_version`
- `forSeatIntg` -> `AppDataResponse.for_seat_intg`
- `airportBusMsg` -> `AppDataResponse.airport_bus_msg`
- `bbrdId` -> `NoticeResponse.board_id`
- `ptwtSqno` -> `NoticeResponse.post_sequence`
- `ptwtTtl` -> `NoticeResponse.post_title`

The inherited `raw` mapping remains caller-accessible for compatibility and
stays excluded from `repr`. No live helper or exception message emits it.
Unknown fields remain available only through `raw`.

## Request And Response Flow

1. The public method builds `{"timeStamp": "<milliseconds>"}`.
2. `KorailHttpClient.get_json()` validates the canonical origin and exact
   method/path allowlist before I/O.
3. The request uses no common member/device form fields and no DynaPath header.
4. Existing HTTP, JSON, base-envelope, session-expiry, and application-failure
   classification runs unchanged.
5. A focused parser converts the validated `BaseKorailResponse` into the
   specialized typed response while preserving `raw`.

Malformed JSON, a missing base envelope, an application failure, a non-mapping
`version`, or a known specialized field that is neither a string nor `None`
raises the existing typed KORAIL error. It must never become an empty successful
model.

## Safety Policy

Add only:

```python
("GET", "/file/CACHE/prdMobilePlusMain.cache")
("GET", "/file/CACHE/prdMobilePlusNotice.cache")
```

The KORAIL HTTP route count becomes 12. `DYNAPATH_ALLOWLIST_PATHS` remains
unchanged, so neither new cache route receives a DynaPath token. The narrower
HTTP allowlist continues to make reservation and other mutation paths
uncallable even though the DynaPath compatibility inventory is broader.

## Live Verification

The existing live helper calls both cache methods before login to verify that
they are account-neutral. Its result adds only:

```python
{
    "appDataLoaded": bool,
    "noticeLoaded": bool,
}
```

No version message, notice title, raw JSON, credential, cookie, advertising ID,
or DynaPath token is returned or printed. The live service remains disabled
unless `KORAIL_MOBILE_API_LIVE=1` and the existing required environment
configuration is supplied.

## Test Strategy

Every behavior is developed with a failing test first.

- Exact route acceptance for the two new GET paths.
- Rejection of wrong methods, off-origin URLs, encoded bypasses, and unknown
  cache paths before transport.
- Exact `timeStamp` query serialization with an explicit deterministic value.
- Default current-millisecond generation with a patched clock boundary.
- Specialized parsing of every known field and nested version fields.
- Preservation and `repr` hiding of `raw`.
- Typed failure for malformed JSON, invalid envelopes, and application errors.
- Public method/export/signature contract updates.
- Live helper call ordering and boolean-only output.
- Regression coverage proving stateful DynaPath behavior is unchanged.

Sanitized fixtures contain only synthetic cache data. They contain no account,
cookie, ticket, PNR, device identity, or token values.

## Files And Responsibilities

- `src/korail_mobile_api/safety.py`: add exactly two cache routes.
- `src/korail_mobile_api/payloads.py`: build and validate the cache timestamp
  query.
- `src/korail_mobile_api/models.py`: define the three new frozen models.
- `src/korail_mobile_api/parsers.py`: parse validated cache responses.
- `src/korail_mobile_api/client.py`: expose the two account-neutral methods.
- `src/korail_mobile_api/__init__.py`: export the new response types.
- `src/korail_mobile_api/live.py`: add the two pre-login reads and bounded
  booleans.
- `tests/fixtures/`: store sanitized app-data and notice responses.
- `tests/`: lock payload, parsing, safety, public surface, and live behavior.
- `README.md`: document the expanded read-only surface.
- `docs/IMPLEMENTATION_PROGRESS.md`: record final verification after the
  implementation is complete.

## Completion Criteria

- The two typed methods work through exact canonical GET routes.
- All failures remain typed and no malformed response is treated as success.
- No DynaPath, session, or existing public-method behavior regresses.
- The full offline suite, wheel/sdist build, and isolated wheel import pass.
- Bounded opted-in live verification succeeds without exposing raw data.
- No mutation route or sensitive material is added.
- The working tree remains uncommitted unless the user explicitly requests a
  commit.
