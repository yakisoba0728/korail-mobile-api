# KORAIL UUID And MAAS Station Expansion Design

**Date:** 2026-07-13

**Status:** Approved for implementation planning

## Goal

Add the two previously runtime-reached, account-neutral KORAIL reads for the
interop UUID value and MAAS station data without adding a MAAS menu, reservation,
payment, cancellation, or other state-changing flow.

## Evidence And Constraints

The APK Retrofit contract and retained runtime inventory identify two calls:

- `GET /ebizcross/getUUID.do` with no query or body fields. The APK response
  extends the common response envelope and adds `mutMrkVrfCd`.
- `POST /ebizmaas/EbizMaasStationList.do` with exactly one form field,
  `addSrvDvCd`. The declared response is the same `StationDataResponse` shape as
  the existing station-data API: `stns.stn[]`.

Both were recorded as HTTP-successful during the 2026-07-09 bounded inventory,
but that evidence did not retain a bounded result code, a usable station count,
or a safe `addSrvDvCd` value. The app obtains `addSrvDvCd` dynamically from a
MAAS menu response and forwards it unchanged. There is no evidenced empty or
fixed default, so the library must require a non-empty caller-supplied value.

Neither path belongs to `DYNAPATH_ALLOWLIST_PATHS`. The implementation must not
attach or generate a DynaPath token for either request.

## Scope

### In scope

- Two exact canonical-origin routes in the read-only registry.
- One parameter-free UUID read.
- One MAAS station-data read with a required additional-service code.
- Typed, repr-safe results with raw data retained only for caller compatibility.
- Offline fixtures, exact transport tests, public-contract tests, redaction,
  bounded live metrics, documentation, package build, and isolated import.

### Out of scope

- MAAS menu lookup or automatic discovery of `addSrvDvCd`.
- Automatic KORAIL-to-SRT handoff.
- MAAS reservation status, cart, reservation, cancellation, or receipt flows.
- Any reservation, payment, refund, check-in, member, point, or mileage mutation.
- Any change to the fixed `rt=0` DynaPath engine or its allowlist.

## Public API

`KorailClient` gains two explicit methods:

```python
def get_uuid(self) -> UuidResponse: ...

def get_maas_station_data(
    self,
    additional_service_code: str,
) -> StationDataResponse: ...
```

`additional_service_code` must be a string containing at least one non-whitespace
character. Validation preserves the caller's exact non-empty value and occurs
before transport I/O.

The package root exports these models:

```python
@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    verification_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class KorailStation:
    code: str
    name: str
    longitude: str | None = None
    latitude: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    stations: tuple[KorailStation, ...] = ()
```

The UUID endpoint name is preserved in the public method because it is the APK
and server contract name. The model uses `verification_code` because the actual
response field is `mutMrkVrfCd`. The value and all raw mappings remain excluded
from repr.

## Request And Response Flow

`get_uuid()` uses `KorailHttpClient.get_json()` with no parameters and no common
fields. It requires the normal KORAIL response envelope, parses
`mutMrkVrfCd` as a non-empty string on a successful response, and retains the
original mapping in the repr-hidden `raw` field.

`get_maas_station_data()` posts exactly:

```python
{"addSrvDvCd": additional_service_code}
```

It sets `include_common=False`; `Device`, `Version`, and `Key` must not be
silently added. Because retained evidence permits envelope-free station data,
the call sets `require_envelope=False`. `KorailHttpClient.post_form()` gains that
keyword with a default of `True`, preserving strict behavior for every existing
caller while accepting either the common envelope or a top-level station payload
for this one method.
The parser requires `stns.stn` to be a list, rejects non-object rows, and requires
each exposed station to contain non-empty `stn_cd` and `stn_nm`. Coordinates are
optional strings. Other server fields remain available only through repr-hidden
raw mappings.

Both operations use `_run_read()` so a recognized session-expiry response clears
local session state consistently. They do not require login and may run before
the login step in the bounded helper.

## Safety And Redaction

The exact read-only route count rises from 12 to 14. Route checks still run before
network I/O and reject alternate hosts, encoded paths, and every unregistered
method/path pair.

`mutMrkVrfCd`, `verification_code`, and spelling variants join the sensitive-key
redaction set. Exceptions may retain raw protocol data for callers but must not
render the verification value, cookies, station raw payload, credentials, or
DynaPath material in `str`, `repr`, logs, or live output.

No method automatically passes the UUID value to SRT or another endpoint.

## Live Verification

The existing opted-in KORAIL live helper adds the UUID call before login and
reports only:

```python
{"uuidLoaded": True}
```

MAAS live verification reads `KORAIL_MAAS_SERVICE_CODE` from the ignored local
environment. When present, it calls the station endpoint before login and emits:

```python
{"maasStationTested": True, "maasStationCount": 1}
```

where the count is the actual bounded station count. When the variable is absent,
the helper performs no MAAS request and emits
`maasStationTested=False, maasStationCount=0`. This is an explicit pending gate,
not a successful MAAS result. The helper never emits the service code, UUID
value, station rows, raw response, cookies, or credentials.

The existing login, cache, station, calendar, train, schedule, transfer, and
ticket-list sequence remains unchanged after these account-neutral calls.

## Testing

Offline TDD coverage must prove:

- the two routes and only those routes increase the registry to 14;
- UUID uses exact GET, an empty query, the canonical origin, and no DynaPath;
- MAAS uses exact POST and the single evidenced form field;
- empty/non-string service codes fail before transport I/O;
- envelope and envelope-free station responses parse into typed models;
- missing, malformed, or non-object station rows fail with typed protocol errors;
- UUID failure, missing code, and non-string code fields fail safely;
- raw values and verification codes are absent from repr, errors, and live output;
- the public method set, signatures, exports, and existing APIs remain stable;
- live-helper fakes cover both the supplied-code and absent-code branches.

After focused tests, run the complete offline suite once, build wheel and sdist,
verify imports in a fresh environment, request an independent read-only review,
and run bounded live verification. A missing MAAS service code must be reported
as the only remaining gate rather than bypassed with an invented value.

## Files Expected To Change

- `src/korail_mobile_api/safety.py`
- `src/korail_mobile_api/models.py`
- `src/korail_mobile_api/parsers.py`
- `src/korail_mobile_api/payloads.py`
- `src/korail_mobile_api/http.py`
- `src/korail_mobile_api/client.py`
- `src/korail_mobile_api/redaction.py`
- `src/korail_mobile_api/live.py`
- `src/korail_mobile_api/__init__.py`
- focused fixtures and tests under `tests/`
- `README.md`
- `docs/IMPLEMENTATION_PROGRESS.md`
