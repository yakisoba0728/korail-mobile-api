# KORAIL verification record

This is the evidence log for `korail-mobile-api`. Until 2026-07-26 it *was* the
README: every claim below was written next to the work that produced it, which
is why it reads as a running audit rather than as a manual. It is kept whole,
and moved rather than summarised, because it is the reason anything in this
package can be trusted — the APK file:line citations behind each field name, the
codes and counts of every bounded live run, and the corrections where an earlier
claim in this document turned out to be wrong.

Read [README.md](../README.md) first if you want to *use* the library. Read this
if you want to know **how a particular claim was established**, or **what a
future operator still has to prove**.

Nothing here is a usage guide, and nothing here is more current than the code:
where this document and the code disagree, the code is right and the disagreement
is a bug report.

## Package boundary and verification summary

The reviewed package boundary contains 60 routes and 80 public methods. All 60
routes are login/read routes: 58 reads plus the login POST and the server-side
logout GET. The eight mutation routes are tracked separately and
are never added to the read-only allowlist. Sixty-four of the methods are the
audited login/read methods, which transmit only read-only requests. The other
fifteen, `reserve`, `reserve_transfer`, `reserve_merge`,
`reserve_with_discount_card`, `confirm_standby_hold`, `cancel_unpaid_hold`,
`pay_with_fake_card`, `pay_with_card`, `refund`,
`verify_offline_refund_ticket`, `execute_offline_refund`,
`register_discount_card`, `extend_discount_card` and `recalculate_price`, are
the consent-gated mutation methods; the remaining two, `begin_non_member` and
`end_non_member`, hold and drop the 비회원 identity locally and transmit
nothing. Each is denied unless the caller supplies a
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
returned money. 환승 (transfer) search and reservation are **implemented and NOT
live-verified** -- see [환승 (transfer) itineraries](#환승-transfer-itineraries)
for the whole shape, what the operator must do to prove it, and the one thing
that blocks a clean reserve → cancel round trip. The
read-only send path continues to refuse every mutation route, so a
state-changing request can leave the process by no other route. The
current reviewed offline gate is `2244 passed, 1 deselected`; the one
deselected test is the explicitly opted-in live-service test. Earlier gates in
this repository's history were `1246 passed, 1 deselected` before the P0
live-evidence documentation coverage and `1247 passed, 1 deselected` directly
after it.

Current service inventory is 32 successful, 10 failed, and 123 unexecuted
entries out of 165.

The original APK and generated decompile directories are intentionally not
committed. Documentation, reproducible inventory output, client source, and
offline contract tests are committed.

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

- [docs/api-endpoints.md](api-endpoints.md): method/path/request parameter/return type inventory.
- [docs/deep-dive/api-contracts.md](deep-dive/api-contracts.md): endpoint-by-endpoint request and response field contract.
- [docs/deep-dive/network-model-fields.md](deep-dive/network-model-fields.md): Java model field catalog from decompiled network classes.
- [docs/deep-dive/webview-and-url-catalog.md](deep-dive/webview-and-url-catalog.md): WebView bridge, URL, scheme, and API-like path catalog.
- [docs/deep-dive/local-storage-catalog.md](deep-dive/local-storage-catalog.md): ORMLite DB model and SharedPreferences key catalog.
- [docs/deep-dive/agent-reports/](deep-dive/agent-reports/): 20 focused subsystem reports.

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

### 환승 (transfer) itineraries

**Implemented and NOT live-verified.** No transfer search and no transfer hold
built by this package has ever been sent to KORAIL. Everything below is read out
of the decompiled app; the section ends with exactly what the operator has to do
to prove it, and with the one thing that currently blocks a clean reserve →
cancel round trip.

KORAIL books a 환승 as **one PNR carrying two journeys**, not as two bookings.
The app does not have a second request builder for it: `C5/a.java:52-119` (`N0`)
is a single loop over the train array it was handed, and the array's **length**
is what decides the whole field set.

| what | 직통 (one leg) | 환승 (two legs) | evidence |
| --- | --- | --- | --- |
| `radJobId` (search) | `1` | `2` | `K4/d.java:5-6`, `DirectInquiryActivity.java:284-296` |
| `txtJrnyCnt` | `1` | `2` | `C5/a.java:55` — from `trainInfoArr.length`, not a flag |
| `txtJrnyTpCd{i}` | `11` on leg 1 | `14` on **both** legs | `K4/e.java:6-7`; `C5/a.java:60` keys on the LENGTH |
| `txtJrnySqno{i}` | `001` | `001`, `002` | `C5/a.java:61` keys on the INDEX, via `DecimalFormat("000")` |
| journey block | 16 keys, suffix `1` | the same 16 keys twice, suffixes `1` and `2` | `OJrny.java:6-27`, `C5/a.java:62-76` |
| cabin | `txtPsrmClCd1` | `txtPsrmClCd1`, `txtPsrmClCd2` | `OSeat.java:16-18`, `C5/a.java:97` |
| seat attribute | `txtSeatAttCd4` | `txtSeatAttCd4`, `txtSeatAttCd4_1` | `OSeat.java:32-35` |
| designated seats | `txtSrcarCnt`, `txtSrcarNo{n}`, `txtSeatNo{n}` | plus `txtSrcarCnt1`, `txtSrcarNo1_{n}`, `txtSeatNo1_{n}` | `OSrcar.java:14-30` |

Two codes are worth stating out loud because guessing them wrongly is easy.
`txtJrnyTpCd` for a transfer is **`14`**, not `12` and not `2` — jadx renders it
as an unrelated same-valued constant, so it was read from bytecode at
`analysis/apktool/smali/K4/e.smali:68`. And it is `14` on **both** legs: the
ternary at `C5/a.java:60` sits inside the per-leg loop but tests the array
length, which `analysis/apktool/smali/C5/a.smali:306-338` confirms by
re-evaluating `array-length` on every iteration. Leg 1 is not left as a direct
leg. The neighbouring `txtJrnySqno` line two lines below *does* key on the loop
index (`smali/C5/a.smali:343`, `if-nez v1`), which is why both were re-read
rather than assumed to match.

**Two legs is a ceiling, not a limit this package chose.** The form has no
journey-3 spelling at all: `OSeat.java:32-35` and `OSrcar.java:21-30` each split
on "journey 1 or not", so a third leg would *overwrite* leg 2 rather than be
added, and `ReservationRequest.java:114-117` reads back exactly the two seat
slots. The search side agrees — `a5/k.java:108-110` builds `{list[i*2],
list[i*2+1]}`, `:156-170` chunks into `new Bundle[2]`, `a5/u.java:252-253`
carries two slots with the second nullable. `KORAIL_MAX_JOURNEY_LEGS` is `2` and
`reserve_transfer` refuses anything else before building a form.

#### Searching

The transfer query moves exactly one field. `search_transfer_trains` sends the
same `seatMovie.ScheduleView` form with `radJobId="2"`, because that is
literally all the app changes: its `WRD000061` dialog handler calls
`setRadJobId(TRANSFER_SQ_NO.getCode())` on the `RsvInquiryRequest` it already
built and hands the object straight on
(`DirectInquiryActivity.java:284-296`, confirmed at
`smali/…/DirectInquiryActivity.smali:1677-1689`). The
`chtnCnt`/`chtnRsStnCd1`/`trnGpCnt`/`trnGpCd1` tail is *not* part of it —
`b5/c.java:154-160` sets those only behind a pinned-환승역 intent extra this
client does not drive.

`search_trains_with_transfer_fallback` is the app's own flow rather than a
convenience: a direct search that finds nothing answers `WRD000061`, and
`DirectInquiryActivity.java:615-624` catches that code **and no other** before
offering the transfer. This client already classifies `WRD000061` as
`KorailNoDirectTrainError`, so that exception is the only one the fallback
swallows.

```python
from korail_mobile_api import TrainSearchQuery, TransferSearchResult

result = client.search_trains_with_transfer_fallback(
    TrainSearchQuery("서울", "여수엑스포", "20260810")
)

if isinstance(result, TransferSearchResult):
    itinerary = result.itineraries[0]
    itinerary.first.train_no, itinerary.second.train_no
    itinerary.transfer_station_name        # None when the legs disagree
    legs = itinerary.legs                  # ready for reserve_transfer
```

**A transfer response is not shaped differently.** It is the same flat
`trn_infos.trn_info` list a direct search returns, and the legs are paired
**positionally**: rows 0/1 are one itinerary, rows 2/3 the next, and a trailing
unpaired row is dropped (`a5/k.java:156-170`, and `:108-110` reading a selection
back out as `{list[i*2], list[i*2+1]}`). `h_chg_trn_seq` is the server's own copy
of that position, `"1"` then `"2"`, corroborated by two independent readers:
`u4/a.java:111-131` de-duplicates a page by dropping a matching `"2"` row
*together with its predecessor*, and `RsvInquiryRequest.java:164-172` seeds the
next page's `txtGoHour` from the last row only when that row is a `"1"`.
`pair_transfer_itineraries` pairs positionally as the app does and treats the
marker as a consistency check — a misaligned list raises rather than producing
two rows that are not one itinerary — while an absent marker is accepted,
because the app defaults it from position too
(`DirectInquiryActivity.java:194-195`).

`transfer_station_name` returning `None` is a real answer, not a parse failure:
`a5/u.java:947-956` prints leg 1's arrival and leg 2's departure as two separate
labels and only collapses them when they are equal, so KORAIL does offer
itineraries that arrive at one station and leave from another.

Transfer paging uses the other half of the cursor. `b5/c.java:370-371` stashes
`h_prcd_trn_no_next` and `h_ectb_trn_no_next` and `:192-194` replays them
through `setSelectTransferPages`, which overwrites `qryStTrnNo` and sets
`qryStTrnNo2` — but only when **both** came back non-empty.
`TransferSearchResult.next_page()` applies that rule;
`TrainSearchContinuation.query_train_no2` defaults to `""`, so a direct next
page puts the same empty string on the wire it always did.

#### Booking

```python
from korail_mobile_api import KorailPassengerCounts, KorailSeatClass, MutationConsent

preview = client.reserve_transfer(
    itinerary.legs,
    consent=MutationConsent(allow_reserve=True),     # dry_run=True by default
    passengers=KorailPassengerCounts(adult=2),
    seat_classes=(KorailSeatClass.GENERAL, KorailSeatClass.SPECIAL),
)
preview.payload["txtJrnyCnt"]      # "2"
preview.payload["txtJrnySqno2"]    # "002"
```

Same route, same consent category, same double-gated send path as `reserve`; the
app uses one endpoint for both. What composes and what does not:

| feature | composes? | why |
| --- | --- | --- |
| passenger mix (`KorailPassengerCounts`) | yes, **per booking** | `OPsg` is built once on the booking-options screen (`w4/a.java:47-74`), before any itinerary exists, and `N0` never touches it |
| cabin class (`KorailSeatClass`) | yes, **per leg** | `C5/a.java:59` reads it with the leg index and `:97` writes `txtPsrmClCd{i}`, so 일반실 + 특실 across legs is a shape the app produces. Pass one value or one per leg |
| 좌석지정 (`SEAT_DESIGNATED`, `1103`) | yes, **per leg** | `C5/a.java:120-133` opens the seat picker once per journey index and passes it as `TRAIN_INDEX`; `SeatSearchActivity.java:675-682` writes `setSrcarCnt(TRAIN_INDEX + 1, …)`. Pass `seats` as one list per leg, one seat per passenger in each |
| 예약대기 (`STANDBY`, `1102`) | **no — refused** | `a5/k.java:120-127`'s `G0()` opens with "if not direct, return false", so `a5/u.java:369-371`/`:401-404` never enables the 예약대기 button on a transfer result; and the app's only `setJobId("1102")` is `DirectInquiryActivity.java:434`, in an `onClick` branch `TransferInquiryActivity` overrides away. Two independent gates |
| 입석+좌석 병합 (`1202`) | not implemented at all | also `DirectInquiryActivity`-only (`:449-450`), and it uses `K4/e`'s other pair, `STANDING_SEAT_1`/`_2` (`21`/`22`) |

`txtStndFlg` is always `"N"` on a transfer, and that is a consequence rather than
a choice. `C5/a.java:78-82` makes the flag a property of the whole itinerary —
leg 1 assigns it and later legs overwrite it only while it still reads `"N"` —
but `S4/J.java:83-85`'s `isStndSeat` needs a 매진 leg, and a 매진 leg is not
bookable: `a5/u.java:346-355` walks **every** leg of the selected itinerary and
disables 예약 outright when any reads 매진 or 좌석부족. The one job that
tolerates 매진 is 예약대기, which does not exist here.

The existing single-leg call is untouched. `reserve` and
`build_reservation_form` emit byte-for-byte what they emitted before, key order
included, and a contract test pins all 56 keys in order.

#### What the operator must do to live-verify

Nothing below has been run.

1. **Find a station pair with no direct service.** This is the whole difficulty:
   the app only offers 환승 after a direct search fails with `WRD000061`. The
   APK names the seven KTX corridors it draws maps for —
   `analysis/apktool/res/values/arrays.xml:200-208`, `ktx_map`: 경부선, 호남선,
   경전선, 전라선, 강릉선, 중앙선, 중부내륙. A pair whose two endpoints sit on
   **different** corridors that do not share a trunk is the shape that forces a
   change of train. Likely candidates, in decreasing confidence: 강릉선 ↔ 전라선
   (e.g. 강릉 → 여수엑스포), 강릉선 ↔ 경전선 (강릉 → 진주), 중앙선 ↔ 호남선
   (안동 → 목포), 동해선 ↔ 호남선 (포항 → 목포). These are inferred from the
   corridor list, **not** verified against a timetable in this repository, which
   holds no real station or route catalogue — every station fixture here is
   synthetic.
2. **Confirm the pair cheaply first.** `get_transfer_stations(dpt, arv)`
   (`qry.chtnStn.do`) is the app's own oracle and is a plain read: a pair with a
   populated 환승역 list is a pair KORAIL expects to be transferred at. Then run
   `search_trains_with_transfer_fallback`; getting a `TransferSearchResult` back
   is the definitive test, because it means the direct query really did answer
   `WRD000061`.
3. **Record the search shape.** With a real transfer response in hand, check the
   claims this package could only infer: that `trn_infos.trn_info` is flat and
   even-length, that `h_chg_trn_seq` alternates `"1"`/`"2"`, and that
   `h_prcd_trn_no_next`/`h_ectb_trn_no_next` are populated (they are the
   transfer paging cursor and no direct response has ever carried them here).
4. **Dry-run the hold first.** `reserve_transfer(..., consent=MutationConsent(
   allow_reserve=True))` returns a `MutationPreview` and sends nothing. Compare
   its payload against the table above before transmitting anything.
5. **Then the hold.** `dry_run=False`, one adult, 일반실, `IMMEDIATE`. Expect
   `h_jrny_cnt` to come back as two journeys.

> **Blocking, and deliberately not fixed here: `cancel_unpaid_hold` cannot
> release a transfer hold.** It requires a hold whose `h_jrny_cnt` is
> numerically one, so a two-journey hold is refused before a form is built. The
> app has no such restriction — `DReservationConfirmActivity.java:269-278`
> passes `reservationResponse.getH_jrny_cnt()` straight through as `txtJrnyCnt`
> alongside the same fixed `txtJrnySqno="0001"` and `hidRsvChgNo="000"` — so the
> fix is to forward the hold's own journey count instead of pinning `"1"`. That
> touches the cancel path, which was explicitly out of scope for this change, so
> it was reported rather than made. **Until it lands, do not send a live
> transfer hold unless you are prepared to cancel it in the KORAIL app or on the
> website**, or it will sit unpaid until KORAIL expires it.

**RESOLVED — this blocker no longer exists.** The record above is kept as
written because it says what was true when the transfer work landed, but the
fix it asks for was made: `build_unpaid_reservation_cancel_form` now echoes the
hold's own `h_jrny_cnt` into `txtJrnyCnt` instead of pinning `"1"`, so
`cancel_unpaid_hold` releases a two-journey 환승 hold and a multi-journey 병합
hold as readily as a single-journey one. Do not read the paragraph above as
current advice: the 2026-07-27 audit found it, and three docstrings that
repeated it, still telling operators a live transfer hold could not be
released — which pushes exactly toward the orphaned hold the code was changed
to prevent.

### 병합예약 (입석+좌석) — one train, split at a mid station

**The first hold is live-verified; the second has never been transmitted.**
`reserve(job_type=MERGE_STANDING)` was sent on 2026-07-26 and answered
`SUCC`/`IRR000018` with `h_jrny_cnt="0002"`, and the server's own 중간연결역
prompt was present in the reply; the hold was cancelled (`IRG000000`) unpaid. No
`reserve_merge` form has ever reached KORAIL.

병합 is the feature whose name most invites the wrong model. It is **not** a
transfer, and it is **not** a third case of the journey loop that builds 직통 and
환승. It is one physical train sold as two journeys so that the two halves can be
seated differently — the app's own words are "구간을 좌석+좌석 또는 좌석+입석으로
연결하여 이용하실 수 있습니다" (`res/values/strings.xml:577`) under the title
좌석 연결역 선택 (`:702`). You board once and never change train.

`K4/e`'s four members are the journey types, and **three of the four reach jadx
as unrelated same-valued constants**, so all four were resolved from bytecode at
`analysis/apktool/smali/K4/e.smali:31-55`:

| member | 이름 | code | jadx rendered it as |
| --- | --- | --- | --- |
| `DIRECT` | 직통 | `11` | (correct) |
| `TRANSFER` | 환승 | `14` | `TicketSelfCheckinStatusActivity.CHECKIN_STATUS_EXCEED` |
| `STANDING_SEAT_1` | 병합 선행 | `21` | `I4.a.BEFORE_DEPARTURE` |
| `STANDING_SEAT_2` | 병합 후행 | `22` | (correct) |

#### The flow is five steps, and two of them are the server's

1. **Eligibility is one flag.** `S4/J.java:61-63`'s `isMixedSeat(cabin,
   h_yms_apl_flg)` is the only row property consulted. Evaluated per cabin it
   collapses to two sets — 일반실 merges on `A`/`G`, 특실 on `A`/`S`
   (`KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`, and `is_merge_eligible`). `a5/u.java:378-380`
   computes it per row and `:394-397` re-labels the booking button 입석+좌석
   예매 (`strings.xml:425`) and sets its tag to `"1202"`.
2. **The first hold is the ordinary direct form with one field changed.**
   `DirectInquiryActivity.java:448-451` reads that tag and does
   `setJobId("1202")`; nothing else moves. `reserve(train,
   job_type=KorailReservationJobType.MERGE_STANDING)` is that call, and a
   contract test asserts the only difference from the live-verified one-adult
   form is `txtJobId`.
3. **KORAIL offers the merge, not the app.** The reply's own message text
   carries the literal `<중간연결역 변경>` (`strings.xml:2018`); `S4/x.java:93-109`
   copies `h_msg_mndry`/`h_msg_txt5` into the confirm screen verbatim, the span
   table at `res/values/arrays.xml:421-438` makes exactly that literal tappable
   (`K6/C5956a.java:74-77`), and tapping it is `setResult(RESULT_OK)` + `finish`
   (`i6/ActivityC5799a.java:70-73`) back to the requestCode-119 caller
   (`C5/a.java:239`). **There is nothing to call at this step.** Whether a given
   hold is mergeable is a property of KORAIL's reply, so an integrator should
   look for that literal in the hold's message text.
4. **`research.mergeSeatsC.do` names the 연결역 and returns the split train.**
   Already implemented: `get_merge_seats_inquiry`. Its `intermediate_stations`
   are the dialog's list and its `trains` are the same train number twice, split
   at the chosen station.
5. **The second hold replaces the first.** The app cancels the standing hold
   (ReservationCancel then ReservationCancelChk —
   `DirectInquiryActivity.java:227-250`; the `AutoRsvCancel*` DAOs are those two
   subclassed only to carry the new trains alongside) and re-books it as one
   reservation of two journeys. `reserve_merge` builds that second hold. The
   cancel is deliberately **not** performed inside it: silently cancelling a
   live PNR under a `"reserve"` consent is precisely the category confusion the
   gates exist to prevent, so the caller runs `cancel_unpaid_hold` under its own
   `"cancel"` consent.

#### Where the merged form diverges from a 환승

Step 5's builder is `DirectInquiryActivity.java:576-601`, not `C5/a.java`'s
loop, and it differs in four ways — all re-read as
`analysis/apktool/smali/…/DirectInquiryActivity.smali:5580-6010`:

| what | 환승 | 병합 | evidence |
| --- | --- | --- | --- |
| `txtJrnyTpCd{i}` | `14` on **both** legs (keyed on array LENGTH) | `21` then `22` (keyed on the loop INDEX) | `smali:5641`, `if-nez v2` |
| `txtStndFlg` | derived from `isStndSeat` per leg | pinned `"Y"` | `smali:5887-5891`, a bare `const-string "Y"` |
| `txtPsrmClCd2` | read per leg — the halves may differ | **copied** from `txtPsrmClCd1` | `smali:5919-5983` |
| `arvTm_` | one per leg, each that leg's arrival | `arvTm_1` only, and it is the **whole route's** arrival time | no `setArvTm` call exists in `smali:5730-6010` |

The last row is the one worth staring at. The merged request is a *clone* of the
`"1202"` hold's (`ReservationRequest.java:29-46`) and `OJrny` merges rather than
replaces (`:158-160`), so the standing hold's `arvTm_1` survives untouched into
a form where leg 1 now ends at the mid station. It is stale on the wire, and
reproducing the app means reproducing it — which is why
`build_merge_reservation_form` takes the standing hold's `TrainSummary` as well
as the two split legs.

`txtJrnyCnt` is `"2"`, `txtJrnySqno` is `"001"`/`"002"` off the loop index, and
`txtJobId` goes back to `"1101"`: the `"1202"` job id belongs only to the hold
being replaced.

#### What the operator must live-verify

Steps 1 to 3 ran on 2026-07-26 (서울→부산 20260731, train 125, one adult) and
are recorded as settled. Steps 4 and 5 have not.

1. **Find a merge-eligible row.** Search any busy corridor near departure and
   look for `TrainSummary.merge_seat_application_flag` in `{A, G}` for 일반실.
   This costs nothing — it is a read. *Settled: train 125 carried
   `h_yms_apl_flg="A"` together with `h_gen_rsv_cd="13"` (매진), which is why
   the availability guard that demanded `"11"` had to go — 입석+좌석 exists
   BECAUSE the seats are gone.*
2. **Dry-run the standing hold**, then send it: `reserve(train,
   job_type=MERGE_STANDING, consent=MutationConsent(allow_reserve=True,
   dry_run=False))`. **This creates a real unpaid 입석 PNR** and must be
   cancelled or paid. Cost: nothing if cancelled promptly. *Settled: `SUCC` /
   `IRR000018`, `h_jrny_cnt="0002"` matching 선행 `21` / 후행 `22`, 43,600 KRW;
   cancelled `IRG000000`, account back to `P100`, no payment.*
3. **Check the reply's message text for `<중간연결역 변경>`.** This was the one
   claim in this section that no amount of static reading could settle: that
   KORAIL puts that literal in `h_msg_mndry`/`h_msg_txt5` of a `"1202"` reply.
   *Settled: the 중간연결역 prompt was present in the live reply, which had
   been inferred from `strings.xml:2018` and `S4/x.java:93-109` and never
   observed until then.*
4. **`get_merge_seats_inquiry`** with that train. Confirm `midStnList` is
   populated and `trn_infos.trn_info` holds exactly two rows carrying the same
   `h_trn_no`. Also a read, so also free.
5. **Cancel the standing hold, then `reserve_merge`.** Expect a hold whose
   `h_jrny_cnt` is two. Cost: nothing if the merged hold is cancelled too.

Still unknown until step 5 runs: whether the merged `"1101"` two-journey form is
accepted at all, and whether KORAIL tolerates the stale `arvTm_1` or validates
it against leg 1's real arrival. That `"1202"` itself is accepted outside the
app's own flow is no longer open — step 2 answered it.

### 정기권 (commuter pass) purchase — NOT implemented, and removed on purpose

**The reads are here and work**: `get_pass_menu`, `get_pass_available_dates` and
`get_pass_schedule` look up pass products, the days a pass may start on, and the
trains it can be bound to. Nothing below takes anything away from them.

**Buying a pass is not here.** It was implemented — `reserve_commuter_pass`,
`pay_for_commuter_pass`, their form builders, models, parser, routes and a
`commuter_pass` consent category — and then **deliberately removed on
2026-07-26**, because neither call can ever be shown to be correct from this
repository:

- A 1개월 정기권 is roughly **₩150,000–₩250,000**, and this package has **no
  refund route and no cancel route** for one. `cancel_unpaid_hold` is the ticket
  cancel and does not take a pass reservation. So a live proof is money that
  cannot be recovered.
- **`passPayIssue` is unreachable in the shipped app** (below), so there is not
  even an app traffic capture to compare a form against. A field list assembled
  from decompiled code, with no capture and no affordable live call, is a
  guess with references.

The knowledge below cost real work to establish and is kept so that nobody has
to rediscover it. What is written here is what the code said; none of it was
ever confirmed on the wire.

#### The purchase is two calls

| call | route | what it does |
| --- | --- | --- |
| 정기권 예약 | `POST pass.passReserve` (`PassService.java:23-25`) | creates an **unpaid** reservation; the reply's `main_info.h_rcvd_amt` is the price |
| 정기권 결제 | `POST pass.passPayIssue` (`PassService.java:19-21`) | **charges that amount** |

#### `passReserve`: twenty `@Field`s from a loop with index-keyed branches

Filled by `CommutationInquiryActivity.java:188-222` (`w0`) from **one** schedule
option's `train_list`. The loop's shape is what determines the field set:

- index 0 fills the origin (`hidAppDptStnCd`/`Nm`) and the first train
  (`hidTrnNo1`/`hidTrnGpCd1`/`hidDtour1`);
- any later index fills the second train (`…2`);
- **every** index overwrites the destination, so the last leg's arrival wins;
- **every** index overwrites the 환승역 — with `""` at index 0 and with its own
  *departure* otherwise.

So a one-train pass sends `hidChtrnStnCd`/`hidChtrnStnNm` as **empty strings**
(assigned on every iteration) but omits `hidTrnNo2`, `hidTrnGpCd2` and
`hidDtour2` **entirely** (never assigned, and Retrofit drops a null `@Field`).
Getting that backwards is the easy mistake; it is the opposite of what the field
list alone suggests.

The twenty fields in declaration order: `Device`, `Version`, `Key`,
`hidCmtrKndCd`, `hidCmtrUtlTrmCd`, `hidCmtrUtlTrmNm`, `hidCmtrUtlAgeCd`,
`hidUseOpenDt`, `hidAppDptStnCd`, `hidAppDptStnNm`, `hidAppArvStnCd`,
`hidAppArvStnNm`, `hidChtrnStnCd`, `hidChtrnStnNm`, `hidTrnNo1`, `hidTrnNo2`,
`hidTrnGpCd1`, `hidTrnGpCd2`, `hidDtour1`, `hidDtour2`.

Everything it needs comes from reads this package still has: `get_pass_menu`
gives the kind code and — importantly — the period **code and display name** as
a pair (`PassPeriodOption`), because `hidCmtrUtlTrmNm` is a real wire field;
`get_pass_available_dates` gives `hidUseOpenDt`; `get_pass_schedule` gives the
trains.

#### `passPayIssue`: both `@FieldMap`s ARE populated by v6.5.0

This is where it stops resembling the discount-card registration, whose second
map the app never fills:

1. **`commPaymentMap` is the entire `passReserve` response.**
   `CommutationInquiryActivity.java:242` is
   `setCommPaymentMap(A.convertObjectToMap(main_info))`, and `S4/A.java:18-27`
   keys every public `get…` by its own name minus `get`, **lowercased**. That is
   54 `h_*` fields, plus two the **app** writes into the object first
   (`:238-240`): `stationInfo` → `stationinfo` (a route label) and `userNames` →
   `usernames` (the holder's name + 님). `isIncludeHoliday` is absent because its
   getter starts with `is`. Ordering is genuinely non-contractual —
   `getMethods()` is unordered and the result is a `HashMap`, so the app itself
   cannot control it, and KORAIL demonstrably tolerates any order.
2. **The second map is the ordinary `PaymentMethod`** — the *same* one a train
   payment sends. `B6/AbstractC1269e.java:736-744` hands the shared payment
   screen's `PaymentMethod` to `CommPaymentDao`, and `V4/a.java:21-34`
   (`getCardRequest`) built it. The card half of a pass settlement is therefore
   byte-identical to `build_card_payment_form`'s card half.

`hidPayAmount` is **not** a caller argument. `AbstractC1269e.java:740` sends
`t1()` = `s1() + getDiscountAmount()`; `s1()` (`:1763`) is the `RECEIVED_AMOUNT`
extra and `getDiscountAmount()` the `DISCOUNT_AMOUNT` extra; and
`CReservationConfirmActivity.java:47-48` sets those two to
`Integer.parseInt(mainInfo.getH_rcvd_amt())` and `0`. So the amount is the
reservation's own `h_rcvd_amt`, and taking it from anywhere else would be
inventing a price. `hidMnsStlAmt1` is the same number for the same reason
(`AbstractC1269e.java:406` → `V4/a.java:27`).

#### Why no capture can exist: `passPayIssue` is dead code in the shipped app

`PaymentActivity.isCommPaymentRequest()` is
`getIPaymentRequest() instanceof CommPaymentDao.CommPaymentResponse` — the
**response** type where a **request** is required (`PaymentActivity.java:502-503`,
confirmed in bytecode at
`analysis/apktool/smali/…/PaymentActivity.smali:3963-3980`). Only
`CommPaymentRequest` implements `IPaymentRequest`
(`…$CommPaymentDao$CommPaymentRequest.smali:1-6`); `CommPaymentResponse` extends
`BaseResponse` and implements nothing (`…$CommPaymentResponse.smali:1-3`). The
test is therefore **always false**, `k1()` falls through executing no DAO, and
the shipped app cannot reach `passPayIssue` at all. The neighbouring
`isPassPaymentRequest()` (`:4415-4430`) tests the **request** type and is
correct, so this is a one-word class-name slip rather than a design.

That is the load-bearing fact. It is why there is no app traffic to compare
against, and why the only remaining way to validate the form is to buy a pass.

#### The `Otr` siblings are a different product

`pass.passOtrReserve` / `pass.passOtrPayIssue` (`PassService.java:39-44`) are the
**자유이용권** family — 내일로, A-PASS, 강릉패스 — booked from
`APassBookingActivity`, `NewAPassBookingActivity` and
`GangneungPassBookingActivity`. `passOtrReserve` takes only
kind/term/age/open-date and no stations or trains at all, because such a pass is
not route-bound; `passOtrPayIssue` adds `h_rcvd_prc` and `hidWctNo` to the scalar
half and its first `@FieldMap` carries a companion list (`h_cmpa_cnt`,
`h_cmpa_nm_N`, `h_cmpa_btdt_N`, `h_cmpa_sex_dv_cd_N` —
`APassBookingActivity.java:546-563`). They were never registered here, and are
not registered now.

#### What bringing the purchase back would cost to prove

Restoring the code is cheap — it is one revert away in this repository's history
(`cd32ea4`, removed in the commit that added this section). Proving it is not:

1. Free: the three reads, and a dry-run of the reserve form against
   `PassService.java:23-25`.
2. **A real unpaid reservation.** `passReserve` at `dry_run=False` costs no money
   directly, but this package has no cancel route for what it creates — release
   it in the KORAIL app or let it expire. This step is the valuable one: its
   `main_info` **is** the payment's first `@FieldMap`, so one real capture
   settles the 54-key list, the empty `hidChtrnStnCd`/`Nm`, and the three absent
   `…2` keys at once.
3. **₩150,000–₩250,000, unrecoverable.** The settlement is the only way to learn
   anything about `passPayIssue`, and it buys one data point: whether a form no
   app has ever sent is accepted. There is no capture to check it against and no
   refund path here. Nobody should spend that to confirm a field list.

Anyone reviving this should also revive its consent posture: a season pass is a
purchase of a different order of magnitude from a train ticket, so it needs its
own `MutationConsent` category rather than a reuse of `allow_payment` — and,
because the settlement carries a PAN in the clear, it must join
`KORAIL_CARD_BEARING_MUTATION_CATEGORIES` so the fake-card / real-card gate
applies to it exactly as it does to a train payment.

### 할인 / 복지 / 쿠폰 surface

**할인카드(N카드)** is the whole 할인카드 feature, and it was entirely absent
before this tranche. Four routes, of which two are reads:

- `get_discount_card_usage_history(card_no)` — `GET ticket.dcntCrdUseQry.do`.
  The trips a card has been spent on.
- `get_discount_card_schedule(request)` — `GET research.dcntCrdScheduleView.do`.
  The trains a card may still be spent on. This is NOT a train search with a
  discount filter: an N카드 is sold against one to three fixed 구간, and the
  route is keyed by the card product and by the section's station NAMES.
- `register_discount_card(request, consent=...)` —
  `POST research.dcntCrdInfo.do`. A **purchase**, despite the name: it answers
  with a `lumpStlTgtNo` that a payment then settles.
- `extend_discount_card(ticket, consent=...)` —
  `GET reservation.dcntCrdExtn.do`. 기간연장. A mutation the app performs with a
  GET, sent through `KorailHttpClient.get_mutation_query`.

The two writes sit in their own consent category, `"discount_card"`
(`MutationConsent.allow_discount_card`, default `False`), which no live path in
this repository touches.

## 운임 재계산 — re-pricing a held PNR

- `recalculate_price(request, consent=...)` —
  `POST certification.PriceReCalculation` (`CertificationService.java:35-37`).
  The app fires it from the payment screen whenever the discount selection
  changes for a reservation that **already exists** (`a6/C1042B.java:265-296`),
  and answers with the same `ReservationResponse` a hold returns — so
  `ReservationHoldResponse.received_amount` comes back as the *new* amount that
  would be settled.

`request.rows` is one `PriceRecalculationRow` per seat of the journey, in seat
order. The first three fields are copied off the held seat — take them from
`get_ticket_reservation_detail` for the same PNR — and the last three carry the
discount being applied:

| field | wire key | source |
|---|---|---|
| `passenger_type_code` | `psg_tp_dv_cd` | seat's `h_psg_tp_cd` |
| `room_class_code` | `psrm_cl_cd` | seat's `h_psrm_cl_cd` |
| `discount_kind_code` | `dcnt_knd_cd1` | seat's existing `h_dcnt_knd_cd1` |
| `requested_discount_code` | `hidDcntKndCd` | the discount being applied, `""` if none |
| `certificate_no` | `hidDscpNo` | its coupon/certificate number, `""` if none |
| `family_sequence_no` | `hidFmlyNo` | 다자녀 `fmlySqno`, `""` otherwise |

**The six lists pair by index.** `k2()` is one loop over a single
`DiscountPriceParams[]` appending one field of the same element to each of six
`ArrayList`s (`a6/C1042B.java:275-283`, confirmed in `smali/a6.1/B.smali`), so
element *i* of all six belongs to seat *i*, and `txtPsgGridcnt` is their common
length. Retrofit flattens each list into **repeated keys** — `addField(name,
element)` in a loop where the name never changes
(`RequestBuilder.smali:1537-1601`) — so the body carries
`psg_tp_dv_cd=..&psg_tp_dv_cd=..`, with no `[]` and no index suffix.

Two derivations the builder enforces rather than trusting the caller, because
both are single code paths in the app and both change money: `"432"` (군장병)
never travels in `requested_discount_code` — the app moves it into
`discount_kind_code` and blanks the field (`S4/D.java:181-183`) — and an
integrated 국가유공자 discount (a `51`-prefixed certificate under kind `"151"`
or `"152"`, `T4/a.java:51-53`) must clear `discount_kind_code` to `"000"`. A
`None` anywhere in the six is refused: Retrofit *skips* a null list element,
which would shorten one key against the other five and re-pair every later row.

It sits in its own consent category, `"price_recalculation"`
(`MutationConsent.allow_price_recalculation`, default `False`) — **not**
`"payment"`, because a payment consent authorises settling an amount that has
already been quoted and this call rewrites the quote. Nothing here has ever
been transmitted and no live path in this repository reaches it.

## 장바구니 담기 — add_to_cart

- `add_to_cart(request, consent=...)` — `POST cart.addCartList`
  (`CartService.java:11-13`). One request field beyond the common three:
  `hidPnrNo` (`AddCartDao.java:9-24`, request class
  `AddCartDao$AddCartRequest`), confirmed independently against
  `AddCartDao$AddCartRequest.smali` (the `hidPnrNo` field declaration) and
  `CartService.smali` (the `@Field("hidPnrNo")` annotation on `addCart` and
  the `@POST("/classes/com.korail.mobile.cart.addCartList")` route
  annotation). `get_cart_list` (`GET` sibling `cart.showCartList`, keyed by
  `pnrNo` rather than `hidPnrNo`) already read the cart; this is the write
  half.

It sits in its own consent category, `"cart"` (`MutationConsent.allow_cart`,
default `False`) — **not** `"reserve"`, because the hold this acts on already
exists and the call creates and destroys nothing this package can observe. It
carries no card number and so is deliberately absent from
`KORAIL_CARD_BEARING_MUTATION_CATEGORIES`. The DAO's response type is a bare
`BaseResponse` (`CartService.java:13`), so `add_to_cart` returns the unparsed
envelope on a live send — the same shape `extend_discount_card` returns for
its own bare-`BaseResponse` route — rather than a dedicated response
dataclass. Nothing here has ever been transmitted and no live path in this
repository reaches it.

Everything starts from `RefundTicketDetailResponse.discount_card`. When the
"ticket" being read is itself a card, `refunds.SelTicketInfo` returns a
`dcnt_crd_info` object carrying the card number, the 기간연장 eligibility flag
and the registered 구간 rows — the card number for the usage read, the station
names for the schedule read.

**A reservation can carry a discount card, and it uses the ordinary reserve
route.** `reserve_with_discount_card(train, card_no=..., consent=...)` POSTs to
`certification.TicketReservation` exactly as `reserve` does. Two fields differ
from the live-verified one-adult 일반실 hold: the eight passenger rows collapse
to a single row spelled `txtDiscKndCd1="153"` + `txtCardNo_1=<card>`, and
`txtMenuId` becomes `"A2"`. Everything else is byte-identical.

**Loyalty and welfare entitlement.**

- `get_korail_point_summary()` — `POST xPoint.MyXPointView`. The my-page
  summary: point balance, 할인쿠폰 and 지연할인권 counts, and — the reason it is
  here — `h_hdcp_flg`, the flag the app uses to decide whether the account has
  a 장애인 registration at all, together with the 장애인증 and 보조견 names it
  renders beside it.
- `get_mileage_history(request)` — `POST mlg.amtSpec.do`. One page of the
  적립/사용 ledger.

`EXCLUDED_API_DOMAINS` narrowed from `"points-mileage"` to
`"points-mileage-write"` to admit those two. The loyalty routes that take a
user-supplied point PASSWORD (`mlg.lpotAthn.do`, `xPoint.XPointView`) stay out:
they answer with `pwdErrTno`, a failure counter, so a wrong guess is a state
change at the loyalty provider whatever the screen calls it.

**Nothing in this surface has been sent to the live server**, and no account
this project can reach owns an N카드. Every request and response shape above
comes from the app's Retrofit declarations and DAOs. What remains open is
server *behaviour*, not shape — see `docs/IMPLEMENTATION_PROGRESS.md` for the
list an operator has to settle.

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
failed, and 124 unexecuted out of 165. The boundary is 58 exact login/read
routes and 72 public methods; the DynaPath allowlist remains six paths.

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
[docs/pass-schedule-read.md](pass-schedule-read.md) for the exact request,
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

Reservation hold, unpaid-hold cancellation, a fake-card payment attempt, an explicitly acknowledged real card payment, and a paid-ticket refund are implemented as consent-gated, dry-run-by-default methods (`reserve`, `confirm_standby_hold`, `cancel_unpaid_hold`, `pay_with_fake_card`, `pay_with_card`, `refund`). `reserve` accepts an arbitrary passenger mix (`KorailPassengerCounts`), either cabin class (`KorailSeatClass`), and any of the booking screen's three job types (`KorailReservationJobType`: immediate `1101`, seat-designated `1103`, standby/예약대기 `1102`), defaulting to the one-adult, general-seat, immediate request. Two adults in a general seat and one adult in 특실 are live-verified (2026-07-26); the other passenger types and any mix of them are static-evidenced only, and the seat-designated (`1103`), 예약대기 (`1102`) and 입석+좌석 (`1202`) variants are all live-verified (2026-07-26), `confirm_standby_hold` included. Real (chargeable) card payment is off by default: it requires `pay_with_card` plus a consent that sets `real_card_acknowledged=True` and `fake_card_only=False`, and `pay_with_fake_card` still refuses anything but a test card. Check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this package version.
