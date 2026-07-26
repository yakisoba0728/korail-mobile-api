# KORAIL Mobile API

This repository provides an installable Python package for the evidenced KORAIL
mobile API surface. It is read-only by default: unless a caller passes an
explicit non-dry-run `MutationConsent`, the client transmits only login/read
requests. It also retains the static reverse-engineering report for `korail.apk`,
Android package `com.korail.talk` version `6.5.0`, as the package's historical
evidence map.

The reviewed package boundary contains 54 routes and 62 public methods. All 54
routes are login/read routes: 52 reads plus the login POST and the server-side
logout GET. The five mutation routes are tracked separately and
are never added to the read-only allowlist. Fifty-six of the methods are the
audited login/read methods, which transmit only read-only requests. The other
six, `reserve`, `confirm_standby_hold`, `cancel_unpaid_hold`,
`pay_with_fake_card`, `pay_with_card`, and `refund`, are
the consent-gated mutation methods. Each is denied unless the caller supplies a
`MutationConsent` that opts into its category; with the default `dry_run=True`
each merely validates its inputs and returns a redacted `MutationPreview` of the
form that *would* be posted, sending nothing. Only a `dry_run=False` consent
performs the live state change, and only through the dedicated double-gated send
path (`post_mutation_form`, which enforces `assert_mutation_route` plus the
consent check).

The pay call transmits the PAN in the clear, so a payment is gated once more on
which kind of card the consent claims. `pay_with_fake_card` still refuses unless
`fake_card_only` is set and therefore still sends only non-chargeable test
cards; that method and that guarantee are unchanged. A real, chargeable card is
possible ONLY through the separate `pay_with_card`, and only on a consent that
explicitly sets both `real_card_acknowledged=True` and `fake_card_only=False` —
the acknowledgement that a real PAN goes over the wire and money actually moves.
Both flags default to the safe side (`fake_card_only=True`,
`real_card_acknowledged=False`), so every consent that does not name the new
flag means exactly what it meant before, and the default posture is still
fake-card-only. The transmit gate independently refuses a payment whose consent
states neither claim or both, so an ambiguous consent is never sent.

`reserve`, `cancel_unpaid_hold`, and
`pay_with_fake_card` were verified end-to-end against the live server (the fake
card was declined, no charge). `pay_with_card` and `refund` have no live-verified
success envelope in this repository: they share the reserve/cancel/pay wire
shapes and the same gated send path, but no run recorded here has settled or
returned money. The
read-only send path continues to refuse every mutation route, so a
state-changing request can leave the process by no other route. The
current reviewed offline gate is `2089 passed, 1 deselected`; the one
deselected test is the explicitly opted-in live-service test. Earlier gates in
this repository's history were `1246 passed, 1 deselected` before the P0
live-evidence documentation coverage and `1247 passed, 1 deselected` directly
after it.

Current service inventory is 32 successful, 10 failed, and 123 unexecuted
entries out of 165.

The original APK and generated decompile directories are intentionally not
committed. Documentation, reproducible inventory output, client source, and
offline contract tests are committed.

## Quick Start

Start here:

1. [docs/korail-apk-analysis.md](docs/korail-apk-analysis.md) - high-level APK, host, network, flow, WebView, storage, and security summary.
2. [docs/api-endpoints.md](docs/api-endpoints.md) - complete Retrofit endpoint table.
3. [docs/deep-dive/README.md](docs/deep-dive/README.md) - deep-dive manual index and reading order.
4. [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) - current package boundary, inventory, and verification state.
5. [docs/RELEASE.md](docs/RELEASE.md) - internal-only test, build, distribution, and fresh-install gate.

Internal editable installation and offline verification:

```bash
python -m pip install -e ".[test]"
PYTHONPATH="$PWD/src" pytest -q
```

Release and handling documents:

- [docs/RELEASE.md](docs/RELEASE.md)
- [SECURITY.md](SECURITY.md)
- [CHANGELOG.md](CHANGELOG.md)

## Current Findings

- Package: `com.korail.talk`
- App version: `6.5.0`
- API version: `250601003`
- Runtime API/Web host: `https://smart.letskorail.com`
- Retrofit method entries: `165`
- Distinct HTTP+path pairs: `159`
- Annotated Retrofit interfaces: `35`
- HTTP methods: `POST 136`, `GET 29`
- Network request/response/model fields cataloged: `2,566`
- WebView JavaScript bridge methods cataloged: `26`
- Parallel deep-dive reports: `20`

## Documentation Map

Core documents:

- [docs/api-endpoints.md](docs/api-endpoints.md): method/path/request parameter/return type inventory.
- [docs/deep-dive/api-contracts.md](docs/deep-dive/api-contracts.md): endpoint-by-endpoint request and response field contract.
- [docs/deep-dive/network-model-fields.md](docs/deep-dive/network-model-fields.md): Java model field catalog from decompiled network classes.
- [docs/deep-dive/webview-and-url-catalog.md](docs/deep-dive/webview-and-url-catalog.md): WebView bridge, URL, scheme, and API-like path catalog.
- [docs/deep-dive/local-storage-catalog.md](docs/deep-dive/local-storage-catalog.md): ORMLite DB model and SharedPreferences key catalog.
- [docs/deep-dive/agent-reports/](docs/deep-dive/agent-reports/): 20 focused subsystem reports.

## Local Artifacts

Ignored local files/directories:

- `korail.apk`: source APK input, not committed.
- `analysis/`: generated `unzip`, `apktool`, `jadx`, and extraction reports, not committed.
- `.DS_Store`: macOS metadata.

Expected local artifact layout after analysis:

```text
analysis/raw/
analysis/apktool/
analysis/jadx/
analysis/reports/
analysis/generated/
```

## Reproducing Static Inputs

Install tools if missing:

```bash
brew install jadx apktool
```

Regenerate decompile artifacts from a local `korail.apk`:

```bash
rm -rf analysis
mkdir -p analysis/raw analysis/reports analysis/generated
unzip -q korail.apk -d analysis/raw
apktool d -f korail.apk -o analysis/apktool
jadx -d analysis/jadx --show-bad-code korail.apk
```

JADX may report decompilation warnings for some library/UI classes. The network layer under `com.korail.talk.network.*` was still readable for the committed documentation. Use `analysis/apktool/smali*` as fallback evidence when Java-like output is ambiguous.

## Scope and Limits

Static analysis remains the evidence source for the APK inventory. The Python
client additionally supports explicitly opted-in live login and read-only smoke
verification using caller-supplied credentials and device identity.

The project does not provide:

- Authentication bypass
- NetFunnel or DynaPath bypass
- Check-in or member mutation APIs (reservation hold, unpaid-hold cancellation,
  a fake-card payment attempt, an explicitly acknowledged real card payment, and
  a paid-ticket refund are provided as consent-gated, dry-run-by-default
  methods; see the mutation section below. Real card payment is off by default
  and reachable only through `pay_with_card` on a consent that sets
  `real_card_acknowledged=True` and `fake_card_only=False`)
- General-purpose runtime WebView automation

Server response values, feature flags, redirect behavior, and server-side
nullable/required rules remain unknown unless evidenced by a controlled,
authorized live observation.

## Python Package MVP

This repository now contains an installable Python client package under `src/korail_mobile_api`.

Default tests are offline:

```bash
pip install -e ".[test]"
pytest
```

### Error taxonomy

Server-side failures are classified on `h_msg_cd`, the field the app itself
branches on, never on Korean message text. Every type below subclasses the one
it replaces, so an existing `except KorailAppError` still catches everything it
used to, and `code` / `message` / `raw` are present on all of them so a caller
can fall back to inspecting the code for a failure that has no subclass yet.

**A failure is decided by `strResult` (plus the app's own `WRC000288`), never by
the code.** Classification chooses which exception describes a failure; it never
decides that there is one. The app works the same way — its dispatcher
recognises a handful of codes and then delivers any *unrecognised* code on a
non-`FAIL` response to `onReceive()` as a success
(`analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:629`). This
is why a warning attached to a success stays a success: `WRR664296`
("…할인은 토/일/공휴일에는 적용되지 않습니다.") arrived with `strResult=SUCC`
and a real, cancelable PNR, and the APK has its own examples — `IRR000014`
(waitlist accepted), `IRT800005` (reserved with a notice), `WRS800036` (per-leg
advisory). `tests/test_error_classification.py` pins that none of them raise.

| Exception | Codes | What a caller should do |
| --- | --- | --- |
| `KorailNoResultsError` | `WRG000000`, `P114`, `P100`*, `WRT300005`* | **Nothing was there.** The request was fine. Retry is pointless; ask a different question. |
| `KorailNoDirectTrainError` | `WRD000061` | No *direct* train. Re-ask the same query as a transfer search — which is exactly what the app does. Subclasses `KorailNoResultsError`. |
| `KorailSoldOutError` | `ERR211161` | **Inventory is gone.** Retry is pointless for this train; pick another. |
| `KorailSeatUnavailableError` | `WRI411345`, `ERR911081`, `WRT800176` | The *seat* you asked for, not the train. Retrying **without** seat designation may work; the app offers exactly that. |
| `KorailReservationRefusedError` | `WRR800029`, `ERR911531`, `ERR911051` | Reserve refused. Look at what you already hold — the app navigates to the user's existing reservations. `message` carries the server's reason. |
| `KorailInvalidRequestError` | `WRG200018`*, `WRT100002`*, `WRT100124`* | **Fix the payload.** A field was rejected; retry is pointless unchanged. |
| `KorailNotEntitledError` | `ERR299943`* | **This account may not book that fare.** The payload is well-formed; it is refused for who is asking. Another account may be accepted with the identical form. |
| `KorailServiceUnavailableError` | `SEMGTK` | The back end is down, not your request. |
| `KorailAppUpdateRequiredError` | `SUPDATE` | This client version is refused. `KORAIL_API_VERSION` has been superseded; no retry interval helps. |
| `KorailAppError` | anything else | Unclassified. `code` and `raw` are intact — this is how the map grows. |
| `KorailSessionExpiredError` | `P058` | **Re-login.** A `KorailAuthError`, deliberately *not* a `KorailAppError`. |
| `KorailDynaPathError` | *(no code — a header)* | **You were flagged, not throttled.** See below. |

Codes marked \* are this repository's own live observations with **zero hits in
the decompiled APK**; every unmarked code is an APK branch, cited file:line in
the class docstring. `classify_app_error` is exported if you want the mapping
without the raising.

**Anti-macro rejection has no message code.** `BaseDaoHelper.java:59-86` reads
the `DynaPath-Result` response header and, when it is negative, displays the
body's `message` *instead of* running the `h_msg_cd` ladder at all
(`BaseActivity.java:632-634`). So the anti-macro refusal surfaces as
`KorailDynaPathError`, not as any `KorailAppError`. srtgo_plus's rule that a
code or message containing `MACRO` means anti-macro (`srtgo/srtgo.py:756`) has
no counterpart in this app and is not encoded; neither is srtgo's second
sold-out code `IRT010110`, which is 0-hit across jadx, all three smali trees,
`analysis/raw` and `analysis/splits`. Separately, KORAIL may attach a macro
*advisory* to a **successful** login via `notiTpCd` in `{MC, MM, MS}`
(`analysis/jadx/sources/S4/u.java:57-90`); that is not a rejection and raises
nothing.

**The library never retries on its own initiative**, and `reserve` in
particular is never retried, because a retried reserve is a duplicate booking.
Classification exists so the *caller* can decide.

One live observation is deliberately **left unclassified**:
`[3]인증정보에 문제가 있습니다.`, seen once on a seat-inventory read after a
burst of calls. No `h_msg_cd` was captured alongside it and the string is 0-hit
in the APK, so there is nothing to key on — classifying it would mean matching
Korean text, the practice this taxonomy replaces. Its trigger is unconfirmed;
rate limiting, a DynaPath problem and a session problem are all consistent with
what was seen. It surfaces as a plain `KorailAppError` with its message intact.

### NetFunnel virtual waiting room

**Implemented, off by default, and partly live-confirmed as of 2026-07-26.**
Probing on that date ran the queue protocol against `nf.letskorail.com` and
settled the three things that had been inferences: the **wire format** is the
native SDK's `<code>:<params>`, the **entry sequence** is `5101` → `5002` → the
gated call → `5004`, and the queue **spans several hosts**. The release path was
exercised end to end and works.

**The `201` queued path is still NOT live-exercised**, because the server was
not queueing: `5101` answered `nwait=0` and admitted us immediately, so nobody
has ever seen this client wait in an actual line. That path — the polling loop,
the ttl sleep and the bounds — remains covered by offline fixtures only, exactly
as the sibling SRT client's polling path is. Treat the handshake as verified and
the wait as built-and-unproven.

It exists for the load at which that stops being true. Enforcement is a
server-side policy and the app ships the client for it, including a **dedicated
peak-season inquiry action, `act_8_2`**, which is a separate queue from the
ordinary `act_8`. Peak season is precisely when a virtual waiting room gets
switched on, and a client with no way to wait its turn simply fails there.

`KorailNetFunnelClient` is a standalone client on the queue's own hosts. It is
not reachable from `KorailClient`, and the two cannot touch each other's origin:
`assert_korail_origin` pins the API to `smart.letskorail.com` — that guarantee is
untouched by anything below, which concerns the queue host only — while the queue
client can reach nothing but `/ts.wseq` on `nf.letskorail.com` and on the queue's
own nodes. `KORAIL_READ_ONLY_ROUTES` stays at 54 app routes with `/ts.wseq`
outside it, so `post_form` and `get_json` can never target the queue.

```python
from korail_mobile_api import (
    KorailClient, KorailConfig, KorailNetFunnelClient, inquiry_action,
)

config = KorailConfig(netfunnel_enabled=True)   # explicit opt-in; default False
queue = KorailNetFunnelClient(config)
client = KorailClient(config)

calendar = client.get_train_calendar()          # the app's own peak-season source
action = inquiry_action(peak_season=is_peak(calendar, query.departure_date))
with queue.slot(action):
    result = client.search_trains(query)
```

`netfunnel_enabled` defaults to `False` and is enforced at construction:
`KorailNetFunnelClient` on a config without it raises `KorailNetFunnelError`
before any socket exists. Enabling it costs a round trip and a failure mode on
every gated operation and buys nothing until the server actually meters us.

**The key is never attached to a KORAIL request.** No Retrofit interface in the
app declares a `netfunnelKey`-shaped field on any route — reserve, pay, cancel
and refund all send exactly what they sent before. The queue is a side channel
that *gates* the call, not a parameter of it, which is why this is a separate
client rather than a header or a form field. The app works the same way: it
runs `T6.g.BEGIN(...)`, and only when the queue answers does it issue the
Retrofit call, releasing the slot afterwards from `BaseDaoHelper`'s
`onPostExecute` — on the success and the failure path alike.

**KORAIL does not speak the JavaScript dialect.** `nf.letskorail.com` serves
both apps, but they embed different client SDKs for the one product. SRT is a
WebView over `netfunnel.js` and sends `nfid`, `prefix`, `js=yes` and a trailing
epoch; `korail.apk` embeds STCLab's native Android SDK (`T6`/`U6`) and sends
none of them. The three requests this library issues are exactly:

| opcode | request | query, in order | host |
| --- | --- | --- | --- |
| `5101` | `getTidChkEnter` — take a ticket | `opcode`, `sid`, `aid` | the front door, `nf.letskorail.com` |
| `5002` | `chkEnter` — enter with it, or ask again | `opcode`, `key` | the node the previous reply named |
| `5004` | `setComplete` — release my slot | `opcode`, `key` | the node that issued the session |

Note that `sid`/`aid` ride on `5101` **only**, which is the opposite of the
JavaScript dialect. `ttl` is never sent back: the native SDK reads it solely to
decide how long to sleep and clamps it to 30 seconds, not the JS bundle's 5. The
reply is `<code>:<params>`, not `<rtype>:<code>:<params>` — confirmed live on
2026-07-26, and `parse_netfunnel_body` still names a `NetFunnel.gRtype=…` body
in its error message, now as a diagnosis for a server that changed rather than
as an admission of guessing.

**The `5101` key is a ticket, not a session, and this is the first trap.**
Sending it to `setComplete` fails with `503:msg="Wrong Server ID"` — which here
means "this key was never exchanged for a session"; see below for the *other*
thing that message means. Only the key `chkEnter` issues can be released, and it
is a different, shorter key:

```
5101 -> 200:key=<252 chars>&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=…
5004 with that key    -> 503:msg="Wrong Server ID"     (sid/aid do not help)
5002 with that key    -> 200:key=<a different, shorter key>&…
5004 with the new key -> 200:key=&nwait=0&…&chk_enter_cnt=0&…
```

So `acquire()` always performs the `5002`, even when `5101` reported `nwait=0`,
and **every step's key supersedes the one before it** — including each `201`
poll. Release the token `acquire()` returned, never an earlier one. A successful
release answers `200:` with an *empty* `key=`, which is a release and not a
truncated body.

Read literally the APK disagrees: its poll loop leaves on any non-`201` status,
so on a `200` from `5101` it sends no `5002` and completes with the ticket. The
live server wins, and the `5002` stays unconditional: the only sequence ever seen
to release cleanly is `5101` → `5002` → `5004`, and whether the ticket would
complete at its own node has never been probed.

**The queue is a POOL, and this is the second trap — diagnosed live on
2026-07-26.** `nf.letskorail.com` is a *front door* that load-balances the entry
call. The node it lands on is the only one that can complete the session, and
every reply names that node in its `ip`/`port`. Sending `setComplete` to the
front door instead therefore fails **about half the time, non-deterministically**
— five acquire-then-release cycles, all entered through the front door:

```
acquire said ip=rnf12.letskorail.com  -> release 503
acquire said ip=rnf12.letskorail.com  -> release 503
acquire said ip=rnf13.letskorail.com  -> release 503
acquire said ip=rnf14.letskorail.com  -> release 200
acquire said ip=rnf13.letskorail.com  -> release 200
```

and the controlled pair that settles it:

```
acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
  release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
  release via rnf13.letskorail.com -> 200:key=&nwait=0&…
```

**`Wrong Server ID` is literal here**, and it is worth an explicit warning
because it reads like a credential or parameter complaint and is neither: the
front door does not own a session that a queue node issued. The two releases that
appeared to work were the balancer happening to land back on the owning node,
which is also why the same key sometimes released fine. Budget an hour for this
message if you meet it anywhere else.

The app has always followed the naming — `T6/d.makeURL` (`T6/d.java:17-19`)
rebuilds the URL from the previous reply's `getHost()`/`getPort()` unless
`host_notmodify` is set, and that flag is `false` by default (`T6/h.java:43`) and
never set by `KTApplication`. This client used to decline it and leaked roughly
half of every slot it took, which is exactly the behaviour NetFunnel exists to
prevent. So the node now rides on the token (`KorailNetFunnelToken.node`) and
supersedes as the key does: a reply naming no node leaves the last one in force,
and a bypass has neither a session nor a node.

**The redirect is constrained, not trusted.** A response choosing where the next
request goes is what an origin guard exists to stop, so the naming is admitted
only into the queue's own pool — `rnf<1-99>.letskorail.com`, lowercase, matched
as whole labels, or the front door itself; `https` on port `443` and no other
port, because the port is not followed on the server's say-so either. Anything
outside that rule is a **hard error**, never a quiet fall-back to the front door:
falling back silently is what produced the flaky release, since it turns "this
reply is lying to us" into "this slot leaked", and a leaked slot makes no noise.
The rule lives in `safety.py` beside the origin assertions, and
`assert_korail_netfunnel_origin` still refuses a node — it guards the configured
origin and the `5101` entry call, so widening one guard cannot widen the other.

Each opcode is registered as an exact ordered query contract rather than the
allowlist being loosened, and `aid` is constrained to the eight action ids
`K4/g.java` declares. Status handling follows the app: `200` pass, `300` bypass
(no key issued), `201`/`202` wait, `301`/`302` `KorailQueueRejectedError`,
everything else `KorailNetFunnelError`. `502` is accepted for `setComplete`
only, and that acceptance is an inference this repository states rather than
hides — the app's `Complete()` never reads its reply at all. `503` is **not**
accepted alongside it: folding "Wrong Server ID" into "released" is precisely
how a slot leaks silently, so it raises with a message naming both of the causes
that produce it — an unexchanged ticket, or the wrong node.

The wait is bounded twice, by poll count (20) and by wall clock (60s), whichever
comes first. The app polls indefinitely behind a dialog a human can close; this
library has no such escape hatch, and a queue is a wait rather than a retry — it
still never retries on its own initiative. The slot is released on both paths,
and a failed release **raises** on the success path rather than being swallowed,
because a silently leaked slot is the failure mode this was written against.

One thing the app does that this client deliberately does not: it runs
`aliveNotice` (`5003`) to keep a waiting-room popup alive. We render no popup.
`5003`, `5105` and `5106` are declared as constants and rejected by the request
guard. The `ip`/`port` naming used to be on this list and no longer is — it is
followed, within the pool rule above, because not following it leaked slots.
`follow_redirects` stays `False` regardless: an HTTP `30x` is a different
mechanism and gets no allowance from any of this.

### Account-neutral cache reads

`KorailClient.get_app_data()` and `KorailClient.get_notice()` expose the two
evidenced account-neutral cache reads:

- `GET /file/CACHE/prdMobilePlusMain.cache`
- `GET /file/CACHE/prdMobilePlusNotice.cache`

Both methods can run before login and send only a `timeStamp` query parameter.
They return frozen typed responses while retaining the original mapping through
the repr-hidden `raw` field. Supplying `timestamp_ms` gives callers a
deterministic cache key; omitting it uses the current Unix epoch in
milliseconds.

### Successful read expansion

The package now exposes 11 new public read methods across the 27 exact login/read routes
registered by the transport boundary:

- Account-neutral: `get_service_status()` and `get_pass_available_dates()`.
- Authenticated account or reservation reads: `get_deposit_banks()`,
  `get_trip_menu()`, `get_cart_list()`,
  `get_delay_discount_tickets()`, `get_discount_coupons()`,
  `get_product_reservations()`, `get_product_detail()`,
  `get_ticket_receipt()`, and `get_reservation_history()`.

All requests use exact GET query or POST form field sets and issue one request
without a fallback. No new DynaPath route was added, and every method above
explicitly disables DynaPath. A bounded 2026-07-15 one-session replay called
only these read methods. Five methods parsed successfully: service status,
deposit banks, discount coupons, trip menu, and reservation history. The cart,
delay-discount, pass-available-date, and product-reservation reads reached
their response parsers but four stopped at `KorailProtocolError`; two
identifier-dependent calls were not issued because the account returned no
owned product or ticket identifiers. No raw response, identifier, message,
credential, cookie, or token was printed or persisted. Subsequent sanitized
shape-only analysis established endpoint-local result-only success envelopes
for cart, delay-discount, and product-reservation lists. Those three routes now
accept only that exact partial-success form while all strict-route, complete
failure, and complete session-expiry behavior stays unchanged. The available
capture did not contain a pass-availability body, so that contract is unchanged.

Deposit-bank and trip-menu reads require an authenticated session. Their
pre-login server responses were complete session-expiry envelopes, so both
public methods now fail locally before transport without a session and the
bounded smoke helper calls them only after its single login.

`WRG000000` from the coupon list and `P100` from reservation history are the
only evidenced no-data application codes converted to typed empty results.
Other failures retain the package's typed error behavior, including `P058`
session expiry and local session clearing.

Product, receipt, cart, and ticket reads accept only caller-owned identifiers.
For example, an already authenticated client can obtain one product detail
without deriving an identifier from another response or making an adjacent
request:

```python
def get_owned_product_detail(
    client,
    reservation_no,
    reservation_sequence,
):
    return client.get_product_detail(
        reservation_no=reservation_no,
        reservation_sequence=reservation_sequence,
    )
```

The reservation, payment, and mutation routes remain excluded from the
read-only allowlist, so no read creates, changes, cancels, pays for, refunds, or
checks in a reservation. State changes occur only through the explicit
consent-gated mutation methods (`reserve`, `confirm_standby_hold`,
`cancel_unpaid_hold`, `pay_with_fake_card`, `pay_with_card`, and `refund`),
never as a side effect of a read.

The package also exposes pure parsers for already-obtained reservation-hold and
reservation-payment JSON: `parse_reservation_hold_response()` and
`parse_reservation_payment_response()`. They return frozen, redaction-safe
models and perform no network request. All five mutation form builders are now
wired to a client method: reservation and unpaid-hold-cancel to `reserve` and
`cancel_unpaid_hold`, the 예약대기 follow-up to `confirm_standby_hold`, card
payment to `pay_with_fake_card` (test cards) and `pay_with_card` (an
acknowledged real charge), and refund to `refund`. Each sends only via the double-gated mutation path and only with a
`dry_run=False` consent; with the default consent each returns a redacted
preview and transmits nothing. `pay_with_card` and `refund` are the two send
paths that, while fully active code rather than blocked, have never been run
against the live server: no run recorded in this repository has settled a real
payment or returned money, so neither has a live-verified success envelope. A bounded
authorized check created one unpaid direct reservation and immediately
completed both cancellation steps; reservation history was empty before and
after, and that check called no payment endpoint. A separate bounded check
attempted one fake-card payment, which the server declined with no charge, and
then cancelled the hold. No PNR, credential, card value, token, or raw response
was printed or persisted.

`reserve` is no longer limited to one adult in a general seat. It takes a
`KorailPassengerCounts` and a `KorailSeatClass`, both keyword-only and both
defaulted so an existing call is unchanged:

```python
from korail_mobile_api import KorailPassengerCounts, KorailSeatClass

preview = client.reserve(
    train,
    consent=MutationConsent(allow_reserve=True),
    passengers=KorailPassengerCounts(adult=2, child=1, senior=1),
    seat_class=KorailSeatClass.SPECIAL,
)
```

`KorailPassengerCounts` has one field per row the app's request carries --
`adult`, `teenager`, `child`, `infant` (동반유아), `senior`,
`severe_disability` (1~3급), `mild_disability` (4~6급) and `guide_dog` -- with
`adult` defaulting to 1 and the rest to 0. It refuses an empty mix, a negative
count and a total above `KORAIL_MAX_PASSENGERS_PER_RESERVATION` (9, the cap the
app's own passenger picker enforces). `txtTotPsgCnt` is every row summed, the
lap infant and the guide dog included, because that is how the app computes it.
`KorailSeatClass` is `GENERAL` (일반실, `"1"`) or `SPECIAL` (특실, `"2"`); a
특실 hold requires the train's *special* seats to be evidenced as available,
not its general ones.

Two adults in a general seat and one adult in 특실 were both live-verified
on 2026-07-26 by reserve->cancel round trips. The 특실 hold read back as
`h_psrm_cl_nm='특실'` with `h_rcvd_amt=83,700` against an `h_tot_prc` of
`59,800`, which is the concrete case that makes the received-amount payment
fix load-bearing. Every other passenger type, and every mix of types, is
still static evidence only, so acceptance, pricing and error envelopes for
those remain unknown until an operator exercises the
specific combinations they need.

### Seat-designated and standby reservations

The booking screen has three actions on the same route, told apart by
`txtJobId`. `reserve` now reaches all three through a keyword-only, defaulted
`job_type` (`KorailReservationJobType`), so an existing call is byte-for-byte
unchanged:

| `job_type` | `txtJobId` | what it is |
| --- | --- | --- |
| `IMMEDIATE` (default) | `1101` | the seat-unspecified hold this package has always sent |
| `SEAT_DESIGNATED` | `1103` | 좌석지정: book named car+seat numbers |
| `STANDBY` | `1102` | 예약대기: join the waiting list on a sold-out train |

**Both variants are live-verified (2026-07-26).** A seat-designated hold booked the exact seats requested, and a standby hold on a sold-out train answered `IRR000014`, its follow-up `IRZ000003`. Compare a booked seat by the inventory's `seat_spec`, not its `seat_no`: the form sends `seat_no` and the reservation detail echoes the `seat_spec` label. Both forms are built from the app's
own request builder; nothing in this repository has transmitted a `1102` or a
`1103`.

#### Seat designation (`1103`)

A caller drives it end to end from the reads that already exist -- search, pick
a train, list its cars, read one car's seat map, name the seats:

```python
from korail_mobile_api import (
    KorailPassengerCounts,
    KorailReservationJobType,
    KorailSeatAssignment,
)

train = client.search_trains(query).trains[0]

cars = client.get_seat_cars(train, passenger_count=2)
car = cars.cars[0]                                   # SeatCar.car_no

inventory = client.get_seat_inventory(train, car.car_no, passenger_count=2)
free = [seat for seat in inventory.seats if seat.sale_possible == "Y"][:2]

preview = client.reserve(
    train,
    consent=MutationConsent(allow_reserve=True),
    passengers=KorailPassengerCounts(adult=2),
    job_type=KorailReservationJobType.SEAT_DESIGNATED,
    seats=[KorailSeatAssignment.from_inventory(inventory, seat) for seat in free],
)
```

`KorailSeatAssignment` carries exactly the two identifiers the seat reads
return and nothing else: `car_no` is `SeatCar.car_no` / `SeatInventoryResponse.car_no`
(`h_srcar_no` / `scar_no`), and `seat_no` is `PhysicalSeat.seat_no` (`seat_no`,
not the human `seat_spec` label). `from_inventory()` pairs them for you and
refuses a seat the read itself marked unsellable.

The form adds exactly five keys per two seats and no others -- `txtSrcarCnt`,
then `txtSrcarNo{i}` / `txtSeatNo{i}` counting from **1** -- appended after the
journey block. `txtSrcarCnt` is the number of *seats*, not cars. An ordinary
`1101` hold sends none of them at all: the app clears its `OSrcar` map and an
empty Retrofit `@FieldMap` contributes no fields, so there is no
`txtSrcarCnt="0"` on the wire (srtgo sends one unconditionally; the app never
does).

**The seat count must equal the passenger total**, counting every row including
동반유아 and 안내견, exactly as the app's own seat map does (its 선택완료 button
is enabled only while `selectedSeatCount == txtTotPsgCnt`). A mismatch is
refused before anything is built or sent, because a partial seat list is how you
get a half-booked hold. Booking the same seat twice is refused too.

#### Standby / 예약대기 (`1102`)

```python
hold = client.reserve(
    sold_out_train,
    consent=MutationConsent(allow_reserve=True, dry_run=False),
    job_type=KorailReservationJobType.STANDBY,
)

client.confirm_standby_hold(
    hold,
    consent=MutationConsent(allow_reserve=True, dry_run=False),
    allow_seat_class_change=True,
    sms_notify=True,
    phone_no="0101234...",
)
```

Standby is *not* gated on the train being sold out, and it is not gated on
seats being available either. The app looks at one field: the search row's
`h_wait_rsv_flg`, which must be the two-character literal `" 9"`
(`KORAIL_STANDBY_WAIT_FLAG`) -- a leading space then a 9. That flag, on the
일반실 tab only, is the sole thing that enables the 예약대기 button; the
availability code is never consulted for it. In practice a train is flagged
that way when it is 매진, which is why standby exists, but the flag is the
rule. korail2 describes the same field as `-2` / `9` / `0`; only the 9 has any
support in this app, and its wire spelling carries the leading space.

Because `1101` demands an available seat and a standby train usually has none,
`reserve` skips that check for `1102` and instead requires the flag and the
일반실 cabin (there is no 특실 standby), and it computes `txtStndFlg` the way
the app does rather than pinning `"N"`.

**Standby is members-only.** The app's reservation request reports itself as
"not non-member enabled" whenever the job id is `1102`, and the session-expiry
handler passes that straight through as "may this be retried as a non-member",
so a 비회원 can never place one. This client satisfies the constraint
structurally -- every mutation requires a logged-in member session and the
non-member booking route is not in the allowlist at all -- and the form carries
none of the non-member identity fields.

A standby booking is **two calls**. The hold comes back with `h_msg_cd =
IRR000014` (`KORAIL_STANDBY_HOLD_MESSAGE_CODE`), which is the only code that
opens the 예약대기 screen in the app; that screen then POSTs
`reservationWait.ReservationWait` with the two options it collects.
`confirm_standby_hold` is that second POST: `txtPsrmClChgFlg` (may KORAIL seat
you in a different cabin when it assigns one) and `txtSmsSndFlg` with
`txtCpNo`, which is sent only when SMS is on and must be 10 or 11 digits. It is
a state-changing call on an existing PNR, so it goes through the same
double-gated mutation transport as everything else, on the **`reserve` consent
category** -- it completes the booking an `allow_reserve` consent authorised,
moves no money and releases no seat, so it is deliberately not a new category.

### Fixed and account-shaped reads

Four static-evidenced, authenticated reads are available as one-request,
DynaPath-disabled operations:

- `get_multi_child_discount_targets(departure_date)` posts to
  `/classes/com.korail.mobile.cust.mchdDcntTgt.do`.
- `get_customer_trip_info()` posts to
  `/classes/com.korail.mobile.research.custTripInfo.do` with fixed
  `medDvCd="03"` and `regSqno="0"`. Its `custMgNo` comes only from the login
  response `strCustNo`; member and member-card numbers are never substituted.
- `get_maas_service_details()` posts the current two-field form to
  `/classes/com.korail.mobile.copt.gdReqQry.do`. A
  `MaasServiceDetailQuery.history(start_date, end_date)` supplies both ordered
  dates for a range of at most three calendar months. This route deliberately
  omits `Key`.
- `get_trip_change_dates(departure_date)` posts to
  `/classes/com.korail.mobile.reservation.tripChgDate.do`.

All four methods require a local authenticated session, validate before
transport, issue exactly one request, and retain raw mappings only behind
`repr=False`. At the historical implementation step, before revalidation, no
live request, credential access, raw capture, or production response was used;
the implementation and tests use static APK contracts, mock transport, and
synthetic fixtures only.

R54 `getTourTrainInfo` has strict internal parser/model coverage for the nested
seat shape, including a required JSON-integer passenger count. Transport is
intentionally held back: there is no `get_tour_train_info` client method, no
registered safety route, and no raw-string request builder. The accepted train
group domain or typed provenance remains unresolved.

Historical pre-revalidation inventory was 28 successful, 9 failed, and 128
unexecuted entries out of 165. The pre-R149 inventory was 31 successful, 10
failed, and 124 unexecuted entries out of 165. Current inventory is 32
successful, 10 failed, and 123 unexecuted entries out of 165. This increment
changes only the package boundary to 54 exact login/read routes and 60 public
methods; it adds no reservation change, booking, payment, refund,
cancellation, check-in, or other mutation capability.

### Bounded next-safe read evidence

A later bounded authenticated read-only revalidation used an empty advertising
ID, logged in once, and confirmed that the repr-hidden `customer_no` was
available. R13 made one request, returned `WRC800029`, surfaced as
`KorailAppError` and was not retried. R32 succeeded with 0 rows, current-form
R43 succeeded with 0 rows, R45 succeeded with 15 rows, and the existing safe
train search succeeded with 10 rows. R52 made zero requests and was recorded
as `skipped_no_typed_leg`; R17, R31, R39, and R54 were not called. No mutation
route was called, and no credential, identifier, or raw response value was
retained.

### Tagged variant and fare reads

Three additional static-contract reads complete the current seven-read tranche:

- `get_gift_ticket_list(request)` accepts only sent history, received history,
  or payment-eligibility request objects. History emits the evidenced blank
  `usePsbFlg=` field; payment eligibility omits dates, that field, and all
  unresolved continuation fields. The route requires a session, forces
  DynaPath off, and makes one request. Its bounded endpoint status remains the
  known HTTP 404; there is no retry, fallback, or alternate path.
- `get_commuter_info(request)` accepts only the closed job `a`, `b`, and `c`
  request variants. Job codes are internal, job `b` preserves grouped repeated
  age-code then passenger-count fields from typed server response data, and job
  `c` carries one repr-hidden original-ticket reference. The uniform public
  wrapper conservatively requires a session and forces DynaPath off.
- `get_price_fare_quote(request)` accepts exactly one or two typed legs plus
  `menu_id`, which defaults to the app's client-side constant `"11"`
  (`a5/k.java:92-94` → `MENU_ID` intent extra → `PriceFareActivity.java:49,62`).
  `txtMenuId` is not a server value: `h_menu_id` occurs nowhere in the app, so
  the earlier requirement that it be read off `TrainSearchMetadata.menu_id` made
  every request built from a real search response raise. It comma-joins
  two legs in response order, derives `chtnDvCd`, and deliberately omits
  `trnCnt` to match shipped bytecode. It does not invent a session precondition
  and retains the existing conditional DynaPath behavior for its already
  allowlisted path.

R39 product-train inquiry has strict synthetic models, an internal exact
request builder, and a full response parser, but still no client method or
safety route. Its `service_1` / `act_6` NetFunnel gate is no longer the reason:
that gate is implemented now (`KorailNetFunnelAction.PRODUCT`, see the NetFunnel
section above). What remains missing is the route registration and the client
method itself. R54 remains parser/model-only until train-group provenance is
closed. `DYNAPATH_ALLOWLIST_PATHS` is unchanged. Historically, this
implementation tranche itself used no live request, credential, `.env`, secure
raw, or production response, and added no reservation, seat-hold, payment,
ticketing, cancellation, refund, or other mutation capability. Its
pre-revalidation inventory was 28 successful, 9 failed, and 128 unexecuted.
The pre-R149 inventory was 31 successful, 10 failed, and 124 unexecuted; the
current inventory is 32 successful, 10 failed, and 123 unexecuted entries out
of 165.

### Ticket-reference reads

Five additional authenticated reads are implemented from static APK contracts
and synthetic/mock evidence only:

- `get_delivery_recipient(ticket)` accepts one exact repr-hidden
  `OriginalTicketReference`.
- `check_ticket_duplication(request)` accepts one closed repr-hidden
  `TicketDuplicationCheckRequest`.
- `get_pbp_acceptance_specifications(tickets)` and
  `get_platform_numbers(tickets)` accept only a nonempty exact tuple of exact
  ticket references. Each `tkRetNo` is derived from its four typed components,
  remains in caller order, and must match the exact integer or decimal-string
  `tkCnt` contract.
- `get_recent_delivery_history()` derives `custMgNo` only from the repr-hidden
  login `customer_no`.

All five methods require a local session, validate before their single request,
force DynaPath off, and use strict full-envelope `SUCC` parsers with repr-safe
nested response models. The implementation used no live request, credential
access, secure raw capture, retry, fallback, or adjacent mutation. At
implementation completion, the pre-R149 inventory was 31 successful, 10
failed, and 124 unexecuted out of 165. The boundary is 54 exact login/read
routes and 62 public methods; the DynaPath allowlist remains six paths.

The ticket-reference implementation itself used no live I/O and added no
mutation capability.

A later bounded authenticated read-only revalidation used an empty advertising
ID, made one successful login call, confirmed logged-in state and
customer-number presence, and called only R149 once. R149 succeeded with one
row and was not retried; R137, R138, R146, and R148 made zero calls. No
mutation, raw response, PII, credential, or server message was retained.
Current inventory is 32 successful, 10 failed, and 123 unexecuted out of 165.

### Static P0 menu and reference reads

Three session-unverified reference methods use static APK evidence and synthetic fixtures only:

- `get_pass_menu(menu_no)` sends one exact `POST` to
  `/classes/com.korail.mobile.pass.passMenu.do`.
- `get_crew_request_list(query_division_code)` sends one exact `GET` to
  `/classes/com.korail.mobile.push.crwCallRq.do`.
- `get_commuter_kind_menu(commuter_kind_code)` sends one exact `GET` to
  `/classes/com.korail.mobile.push.cmtrKnd.do`.

Each method requires its caller-supplied runtime discriminator and has no
default or library-selected code. Server-returned pass, period, age, and crew
option codes remain typed response data. All three requests use their exact
four-field contracts (`Device`, `Version`, `Key`, plus the discriminator),
issue no fallback request, and explicitly disable DynaPath. No live request or
raw response body was used to implement or verify this increment.

The current client has no local session precondition for these calls, but that
does not establish the live server's authentication requirement. Treat all
three as session-unverified and perform live verification only after login.

The similarly named `/classes/com.korail.mobile.push.callCrew.do` route is the
state-changing crew-call operation and remains excluded from the transport
allowlist and public client. Reading crew request options never submits a crew
call.

### Pass schedule candidate read

`get_pass_schedule(request)` exposes the statically evidenced
`POST /classes/com.korail.mobile.pass.passScheduleInfoList` candidate lookup.
Its frozen request requires every train, date, route, page, and pass value from
the caller; it does not hardcode runtime menu or pass codes. The client sends
one exact form with DynaPath disabled and accepts only a full `SUCC` envelope.

The server's session rule remains unverified. Until a bounded live check can
run after login, the client conservatively requires an authenticated session
and the route is not documented as account-neutral. The API stops before the
separate reservation and payment routes. See
[docs/pass-schedule-read.md](docs/pass-schedule-read.md) for the exact request,
typed response, and live-validation boundary.

### Typed car and physical-seat inventory reads

Version `0.2.0` adds `get_seat_cars(train, *, passenger_count=1)` and
`get_seat_inventory(train, car_no, *, passenger_count=1)`. Both methods require
an authenticated session and consume only server-owned schedule fields already
present on `TrainSummary`. Caller counts and every required train field are
validated before Sid generation or transport.

This first increment is deliberately fixed to main menu `11`, general room
class `1`, seat attribute `015`, an empty product number, and an empty control
division. Each method generates one fresh Sid and issues one exact POST. The
forms omit `sidTest`, pass `Device`, `Version`, and `Key` explicitly, and force
`include_common=False` plus `include_dynapath=False`. No custom field map,
generic route escape hatch, seat selection, hold, or reservation action is
exposed.

The returned car, seat, and window collections are immutable tuples. Raw
mappings, response messages, train and seat identifiers, and the documented
banner URL are repr-hidden. The banner URL remains inert response data and is
never followed by the client.

### Raw-backed typed response core

The raw-backed typed response core now returns `StationInfoResponse`, the
existing `StationDataResponse`, `TrainCalendarResponse`,
`TrainScheduleResponse`, and `TransferStationListResponse` from the five
already-public reference and schedule reads. Calendar days, actual-schedule
stops, and transfer stations are frozen typed rows. Normal station data also
exposes optional group, major, coordinate, and popup metadata; popup messages,
titles, and URLs are repr-hidden.

`TrainSearchMetadata` promotes the response menu, job, product, paging, and
count strings. Those paging strings are now wired: `TrainSearchResult.next_page()`
returns a `TrainSearchContinuation` (or `None` once the server stops setting
`h_next_pg_flg="Y"`, the app's own stop condition), and
`search_trains(query, continuation=...)` replays it into the request's
`qryStNo`/`qryStTrnNo`/`pgPrCnt` exactly as the app does. The five paging fields
`qryDvCd`, `qryStNo`, `qryStTrnNo`, `qryStTrnNo2`, `pgPrCnt` are sent on every
search, first page included, because the app sets them unconditionally.
`TrainSummary` now promotes station construction orders,
seat-attribute and car-type fields, train class/group names, reservation
availability, and remaining-count metadata needed by safe follow-on reads.
The observed `h_std_rest_seat_cnt`, `h_fst_rest_seat_cnt`,
`h_free_sracar_cnt`, and `h_rsv_wait_ps_cnt` values remain optional strings;
the client does not sum, coerce, or infer numeric meaning from them.

For compatibility, existing constructor prefixes are preserved through
appended, defaulted fields. Client call parameters remain unchanged; return
annotations for five existing read methods are narrowed to typed responses.
Existing routes, methods, and request payload semantics remain unchanged.
Response and nested raw mappings remain `repr=False`, as do newly promoted
server identifiers, URLs, and free-text messages. This typing increment does
not use the promoted values to change the fixed seat request forms.

Retained raw replay also established that station `popupType` and actual
arrival delay count may arrive as either JSON integers or finite ASCII decimal
strings. Both forms normalize to typed integers; empty, signed, non-ASCII,
boolean, and floating-point values remain rejected.

The separately opted-in evidence command is not part of the broad live smoke:

```bash
KORAIL_MOBILE_API_LIVE=1 PYTHONPATH="$PWD/src" \
  python3 scripts/capture_seat_inventory_evidence.py \
  --output /tmp/korail-seat-inventory-result.json --force
```

It permits at most one login operation, one minimum train search, one car-list
call, and one first-car seat-list call. Its atomically written JSON is limited
to fixed statuses, 0/1 operation counters, counts capped at 10,000, documented
field/type-presence booleans, and a sufficiency category. It suppresses raw
responses, messages, identifiers, dates, stations, credentials, session data,
Sid values, tokens, and URLs. A bounded live structural run selected the first
app-eligible general-room result and received `IRG000000`/`SUCC` from both
read routes: 5 cars and 75 seat rows. The response used the documented field
types, allowed a missing floor and an empty window collection, and contained
repeated seat labels; the client preserves those repeated rows and their
original order. The evidence retained no raw response, identifier, message,
station, date, credential, cookie, Sid, token, or URL. A later post-fix helper
confirmation stopped at the service-status preflight before login transport,
so it made no search, car-list, or seat-list request and was not rapidly
retried.

### P0 train reads and bounded live evidence

Four additional APK-evidenced read operations are exposed through closed,
frozen request objects. Initial implementation used only static APK evidence
and synthetic fixtures. That history remains the basis for the closed request
contracts and offline parser coverage.

| Public method | Frozen request | Documented APK name and exact route |
|---|---|---|
| `get_free_seat_car_info(request)` | `FreeSeatCarRequest` | `getFresScar`; `POST /classes/com.korail.mobile.trn.fresScar.do` |
| `get_guide_seat_condition(request)` | `GuideSeatConditionRequest` | `getGuideSeatCnd`; `POST /classes/com.korail.mobile.reservation.guideSeatCnd.do` |
| `get_seat_assignment_schedule(request)` | `SeatAssignmentScheduleRequest` | `getAssignScheduleView`; `POST /classes/com.korail.mobile.research.assignScheduleView.do` |
| `get_merge_seats_inquiry(request)` | `MergeSeatsInquiryRequest` | `getMergeSeatsInquiry`; `POST /classes/com.korail.mobile.research.mergeSeatsC.do` |

A later bounded authenticated revalidation made 28 requests and received 28
responses. It produced 25 successful operations, one expected typed
application failure, and three input-dependent skips. Deposit-bank and
trip-menu reads succeeded after login. R30 `getFresScar` returned exact
`strResult="SUCC"` and parsed successfully. R33 `getGuideSeatCnd` returned a
full `FAIL` application envelope for the server-supplied seat attribute; it
surfaced as `KorailAppError` and was not retried. R37
`getAssignScheduleView` and R51 `getMergeSeatsInquiry` remain static-only and
unexecuted. Because the bounded run was authenticated, it does not establish
pre-login server behavior for these four routes. Offline raw replay yielded 27
parsed responses, one expected
`KorailAppError`, and zero unexpected failures. No raw response value,
identifier, credential, cookie, token, or server-supplied seat attribute was
recorded.

The Java names above are documentation aliases only; the client does not add
duplicate camelCase methods. Each public method accepts exactly its matching
request type, composes the documented form with `Device`, `Version`, and `Key`,
issues one POST, and forces `include_dynapath=False`. The forms cannot accept a
caller-supplied mapping or additional wire field. Date/time shapes, ASCII train
and order identifiers, transfer type, and passenger counts are validated
before transport.

These reads do not require a local authenticated-session precondition because
their requests contain no account, PNR, ticket, payment, or point identifier.
They require the full envelope and exact success value `strResult="SUCC"`.
Existing `FAIL`/`WRC000288` application errors remain typed failures, and a
server `P058` clears any existing local session before raising
`KorailSessionExpiredError`.

The schedule responses share an immutable `TrainScheduleItem` representation;
the merge response additionally exposes immutable intermediate stations. Raw
mappings, train/station/car identifiers, and server free text are repr-hidden.
This phase deliberately does not accept `TrainSummary` and adds no convenience
chaining from a search result, seat selection, reservation, fallback request,
or live helper call.

### Static-only limousine schedule and seat reads

Three additional P0 wrappers expose the APK's read-only limousine contracts:

- `get_limousine_schedules(query)` maps the direct schedule-list response.
- `get_limousine_seat_inventory(query)` maps the selected train/car seat list.
- `get_limousine_schedule_view(query)` maps the Sid-bearing schedule-view
  response and its typed train/product rows.

Each method accepts one frozen, closed request dataclass. The schedule and seat
queries require caller-supplied service, schedule, train, and car identifiers;
the schedule-view query additionally requires a caller-supplied menu and job
identifier. The package does not embed the APK's current limousine service,
menu, train-class, station, car, seat-attribute, or sale-division values.
Unknown wire fields cannot be supplied.
Only the exact public query dataclass types are accepted; subclasses are
rejected before Sid generation or transport.

All three methods issue exactly one POST with the Retrofit-declared field set
and `include_common=False`. The first two forms explicitly carry `Device`,
`Version`, and the app `Key`; the schedule-view form carries `Device`,
`Version`, and one fresh `Sid`. None has a static authenticated-session
prerequisite in the reviewed caller flow, so a login is not required. Existing
session-expiry handling still clears an already-present local session on
`P058`. The three calls are DynaPath-disabled because none of their exact paths
appears in the APK DynaPath URL list.

Responses use frozen typed schedule, train, recommended-product, and
seat-inventory models. Identifiers, raw mappings, response/free-text messages,
and station names are repr-hidden. These methods expose no seat selection,
seat hold, booking, reservation, payment, cancellation, or fallback request.
No live call was made for this increment; its contract and parser evidence is
limited to exact APK/static sources plus synthetic fixtures.

### UUID and MAAS station reads

`get_uuid()` performs the parameter-free account-neutral UUID read.
`get_maas_menu_list()` performs the generic MAAS menu read used by the app's
main booking screen. It sends only `Device` and `Version`, parses the server's
`menuList[]`, and exposes each `menuList[].addSrvDvCd` as a repr-hidden
`additional_service_code`.
`get_maas_station_data(additional_service_code)` requires the service code that
the official app obtains dynamically. The library has no empty or fixed
service-code default.
None of these requests uses DynaPath, and none of these methods starts a
reservation or passes the UUID value to SRT automatically.

Controlled live evidence showed that the UUID success response can contain a
valid non-empty verification field with only a partial common envelope.
`get_uuid()` therefore opts into relaxed common-envelope decoding for this
request only. The transport default, existing POST behavior, and every other
caller's strict-envelope behavior remain unchanged.

Bounded live verification reads the menu first and selects at most one active
station-capable item using the app's `active` and `appData` routing rules.
`KORAIL_MAAS_SERVICE_CODE` remains an explicit override in the ignored live
environment; it is not a hardcoded service-code source. If no eligible item or
override exists, the helper reports `maasStationTested=false` and performs no
station-list request.

Live smoke is opt-in and limited to login plus read/query calls. DynaPath
device identity values must be supplied explicitly.
KORAIL_ADVERTISING_ID is optional and defaults to an empty string:

```bash
export KORAIL_MOBILE_API_LIVE=1
export KORAIL_MEMBER_NO="<member-id>"
export KORAIL_PASSWORD="<password>"
export KORAIL_DYNAPATH_DEVICE_ID="<android-id>"
export KORAIL_DYNAPATH_OS_VERSION="<android-version>"
export KORAIL_DYNAPATH_DEVICE_MODEL="<device-model>"
export KORAIL_ADVERTISING_ID=""
python3 -c "from korail_mobile_api.live import run_live_smoke_from_env; print(run_live_smoke_from_env())"
```

The helper performs both cache reads and the generic MAAS menu read before
login, then performs the session-coupled deposit-bank and trip-menu reads after
its single login. It emits only booleans, status codes, and bounded counts. Its
metadata is limited to fields such as `appDataLoaded`, `noticeLoaded`,
`maasMenuCount`, `depositBankCount`, and `tripMenuCount`; it does not return raw
account, session, ticket, station, menu, app-data, or notice response bodies.

For the successful-read expansion, the pre-review complete offline suite result
of `427 passed, 1 skipped` is historical. The independent final whole-feature
review reported Critical 0, Important 2, and Minor 0. Both Important findings
were fixed together in `6b25341`, with `192 passed` focused coverage; no open
Critical or Important finding remains. Fresh post-fix verification reported
`435 passed, 1 skipped`; the only skip was the explicit live-service opt-in.

A fresh isolated build produced one wheel and one source distribution, and a
temporary environment installed the wheel and imported `KorailClient` plus all
11 new response types from `site-packages`. The installed package reported
`routes=25`, `public_methods=28`, and `response_types=11`. A fresh static scan
reported `request_literals=27` and `excluded_mutation_routes=0`; the full
feature diff passed `git diff --check`, and the DynaPath files remained
unchanged.

Before this expansion, the corrected UUID contract's tracked Task 6 result was
`275 passed, 1 skipped`, 15 registered routes, and successful isolated imports
of `KorailClient`, `MaasMenuItem`, and `MaasMenuListResponse`. Independent Task
6 spec and quality reviews for that preceding UUID/station phase passed with no
findings.

Independent review confirmed the UUID-only correction changed no routes,
DynaPath behavior or allowlist, existing POST/default behavior, or public API
surface. Final cleanup removed generated package/build artifacts and the
temporary isolated-install environment; the normal Git working tree was clean.

The single corrected bounded live invocation succeeded with
`appDataLoaded=true`, `noticeLoaded=true`, `uuidLoaded=true`,
`loggedIn=true`, `commonCode=API.I00000`, `stationInfoLoaded=true`,
`stationDataCount=281`, `calendarCode=API.I00000`, `trainCount=10`,
`scheduleCode=IRZ000001`, `transferCode=IRZ000001`, and
`ticketCode=WRT300005`. A subsequent bounded MAAS check fetched 11 generic menu
items, identified 4 station-capable items using the app's routing fields, and
made one station-list request with the first server-provided code, returning
101 stations. No service code, menu name, URL, sensitive value, or raw response
is recorded here. An earlier pre-correction live attempt stopped at UUID
envelope validation, which led to the endpoint-specific partial-envelope
correction above.

DynaPath is supported for the documented allowlist paths. Runtime constants
such as `Device`, API version, app key, DynaPath header name, and allowlist paths
are importable from the package. Live smoke constructs `DynapathTokenSettings`
only from required caller-supplied environment values and fails before request
construction when any required identity value is missing.

The built-in generator follows the successful fixed `rt=0` contract: SDK version `v1.0.3`
(matching decompiled `com.korail.talk` v6.5.0, `B/C1229b.java:137,157`),
four random characters drawn from the app's own 62-character nonce alphabet
`a-zA-Z0-9` (`b/C1229b.java:164`, confirmed in smali at `b.1/b.smali:549`), and
exactly one
`rt=0` field in each token payload. An earlier version of this document
described that alphabet as uppercase-and-digits only; that was a 36-character
subset the APK contradicts, and it made roughly 89% of genuine app nonces
unreachable. The app-start timestamp is captured once
when live configuration is built; request history is not accumulated. The raw
application-signature setting is form-encoded exactly once during token
construction.

When enabled, the client attaches `DYNAPATH_HEADER_NAME` only for the documented
DynaPath allowlist paths. Callers that need an external implementation may
still provide a custom `DynapathConfig.token_provider`; the package contains no
separate probe generator and does not retain request history. Login follows the
app sequence and treats only `IRZ000001` or `S200` as final success.

Reservation hold, unpaid-hold cancellation, a fake-card payment attempt, an explicitly acknowledged real card payment, and a paid-ticket refund are implemented as consent-gated, dry-run-by-default methods (`reserve`, `confirm_standby_hold`, `cancel_unpaid_hold`, `pay_with_fake_card`, `pay_with_card`, `refund`). `reserve` accepts an arbitrary passenger mix (`KorailPassengerCounts`), either cabin class (`KorailSeatClass`), and any of the booking screen's three job types (`KorailReservationJobType`: immediate `1101`, seat-designated `1103`, standby/예약대기 `1102`), defaulting to the one-adult, general-seat, immediate request. Two adults in a general seat and one adult in 특실 are live-verified (2026-07-26); the other passenger types and any mix of them are static-evidenced only, and **neither the seat-designated nor the standby variant has been live-verified** — including `confirm_standby_hold`, the second call a standby booking needs. Real (chargeable) card payment is off by default: it requires `pay_with_card` plus a consent that sets `real_card_acknowledged=True` and `fake_card_only=False`, and `pay_with_fake_card` still refuses anything but a test card. Check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this package version.
