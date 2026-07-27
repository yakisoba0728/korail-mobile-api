# korail-mobile-api

A Python client for the API the KORAIL (한국철도공사) Android app talks to. It
logs in, searches trains, reads your tickets and reservations, and — only behind
an explicit consent object — holds a seat, cancels, pays and refunds, using the
same routes and the same form fields the app itself sends.

Three things to know before you install it:

- **It is reverse-engineered, not documented.** Every route, field name and
  status code here was read out of a decompiled `com.korail.talk` 6.5.0 APK and,
  where it could be afforded, confirmed against the live service. KORAIL
  publishes no specification and promises nothing about stability.
- **It talks to the real service.** `smart.letskorail.com` is production
  ticketing. A reservation this library makes is a real reservation somebody has
  to cancel, and a payment is real money.
- **It is not affiliated with, endorsed by, or supported by KORAIL.** Use your
  own account, accept the consequences yourself, and read
  [SECURITY.md](SECURITY.md) before you report anything.

## Install

There is no PyPI release. Install it from this repository:

```bash
pip install "korail-mobile-api @ git+https://github.com/yakisoba0728/korail-mobile-api"
```

Python **3.11 or newer** (`requires-python = ">=3.11"`). The only runtime
dependencies are `httpx` and `cryptography`. The package is typed and ships
`py.typed`.

For a checkout you intend to edit:

```bash
pip install -e ".[test]"
python3 -m pytest -q -m "not live"
```

## Quickstart

This logs in, searches, and reads something back. It sends nothing that changes
state and touches no money.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
client.login("<member no, email, or phone>", "<password>")

result = client.search_trains(
    TrainSearchQuery("서울", "부산", "20260810", departure_time="080000")
)
for train in result.trains[:5]:
    print(
        train.train_no,
        train.departure_time,
        train.arrival_time,
        train.general_availability_name,   # 예약가능 / 매진 / …
    )

summary = client.get_korail_point_summary()
print(summary.korail_point, summary.discount_coupon_count)

client.logout()
client.close()
```

Stations may be given as names (`"서울"`) or as codes; a numeric reference is
resolved through the station list the app itself downloads. Dates and times are
the app's own `YYYYMMDD` and `HHMMSS` strings.

Nothing above needs DynaPath. That anti-automation header is **off by default**
and is only ever attached to the six allowlisted paths, from settings you supply
explicitly — see [docs/verification-record.md](docs/verification-record.md).

## What it can do

The reviewed package boundary contains 60 routes and 84 public methods. Fifty-eight
of the routes are reads, plus the login POST and the logout GET; the fourteen
mutation routes are tracked in a separate set and are never added to the
read-only allowlist. Eighteen of the methods are consent-gated mutations; the
remaining sixty-six transmit only login/read requests, or nothing at all.
The other twelve are the consent-gated mutations below.

### Searching and reading

| What you want | Method |
| --- | --- |
| Trains on a date | `search_trains(query)`, paged with `result.next_page()` |
| Trains when there is no direct one | `search_trains_with_transfer_fallback(query)`, or `search_transfer_trains(query)` outright |
| Which stations a pair may be transferred at | `get_transfer_stations(dpt, arv)` |
| Cars and the physical seat map of one car | `get_seat_cars(train)`, `get_seat_inventory(train, car_no)` |
| Where a train actually stops, and when it runs | `get_train_schedule(...)`, `get_train_calendar()` |
| The station catalogue | `get_station_data()`, `get_station_info()` |
| Your tickets and one ticket in detail | `get_ticket_list()`, `get_ticket_reservation_detail(request)` |
| Your reservations and purchase history | `get_reservation_history()`, `get_product_reservations(...)` |
| What a refund would cost, and what a ticket is | `get_refund_commission(ticket)`, `get_refund_ticket_detail(ticket)` |
| Points, coupons, welfare flags, mileage ledger | `get_korail_point_summary()`, `get_mileage_history(request)` |
| Limousine-bus schedules and seats (static-evidenced, never live-run) | `get_limousine_schedules(query)`, `get_limousine_seat_inventory(query)`, `get_limousine_schedule_view(query)` |

Plus the account-neutral reads that need no login at all: `get_service_status()`
(is the service up, before you do anything else), `get_app_data()`,
`get_notice()`, `get_uuid()`, `get_maas_menu_list()` and
`get_maas_station_data(code)`. The whole login/read surface, with the exact
route behind each method, is in
[docs/api-status-by-service.md](docs/api-status-by-service.md).

### Booking

One method, `reserve`, reaches all four of the booking screen's actions through
a keyword-only `job_type`, so an unadorned call sends exactly what it always
sent:

| `job_type` | `txtJobId` | What it books |
| --- | --- | --- |
| `IMMEDIATE` (default) | `1101` | An ordinary seat-unspecified hold |
| `SEAT_DESIGNATED` | `1103` | 좌석지정 — named car and seat numbers from `get_seat_inventory` |
| `STANDBY` | `1102` | 예약대기 — join the waiting list on a sold-out train; completed by `confirm_standby_hold` |
| `MERGE_STANDING` | `1202` | 입석+좌석 — the first of the two holds 병합예약 needs; the second is `reserve_merge` |

`reserve` also takes a `KorailPassengerCounts` (eight passenger rows, capped at
nine people) and a `KorailSeatClass` (일반실 or 특실).

One trap worth knowing before you use `SEAT_DESIGNATED`: a seat carries two
identifiers. The form sends `KorailSeatAssignment.seat_no`, and the reservation
you read back echoes the human label `seat_spec` — so compare a booked seat by
`seat_spec`, never by `seat_no`, or a correct booking will look wrong.

Two more entry points share the same route and the same `reserve` consent:
`reserve_transfer(legs, ...)` books a 환승 as one PNR carrying two journeys, and
`reserve_with_discount_card(train, card_no=...)` books the single 할인카드
passenger row.

### Cancelling, paying, refunding

- `cancel_unpaid_hold(hold, consent=...)` — release a hold before it is paid.
- `pay_with_fake_card(hold, card, consent=...)` — settle with a non-chargeable
  test card. It refuses anything else.
- `pay_with_card(hold, card, consent=...)` — settle with a real card. Off by
  default; see the safety model.
- `refund(ticket, consent=...)` — refund a paid ticket.
- `recalculate_price(request, consent=...)` — 운임 재계산: rewrite what an
  existing hold will cost when the discount selection changes.

There is a second, unrelated refund path for a paper ticket bought at a station
window, with nobody logged in. It identifies the ticket by the 16-digit
반환번호 printed on it plus the requester's name, so it starts by holding a
비회원 identity rather than by logging in:

```python
client.begin_non_member(requester_name, requester_phone)   # sends nothing
verified = client.verify_offline_refund_ticket(
    OfflineRefundReturnNumber.from_ticket_number(printed_ticket_number),
    consent=MutationConsent(allow_refund=True),   # dry run: returns a preview
)
result = client.execute_offline_refund(verified, consent=...)
```

Both take the same `allow_refund` consent as `refund` — the same act on the
same money, only a different way of proving whose ticket it is — and both
refuse to run while a member session is active. `verify_offline_refund_ticket`
is consent-gated even though the app calls it 조회, because what it returns is
the ticket's return password, which the second call spends.
`result.is_refund_completed` tells you whether the money came back now or the
paper ticket still has to be handed in at a station within a year.

### Discounts, welfare and passes

- `get_discount_card_usage_history(card_no)` and
  `get_discount_card_schedule(request)` read an N카드: what it has been spent
  on, and the trains it may still be spent on.
- `register_discount_card(request, consent=...)` buys one;
  `extend_discount_card(ticket, consent=...)` is 기간연장. Both sit in their own
  `discount_card` consent category.
- `get_pass_menu(menu_no)`, `get_pass_available_dates(...)` and
  `get_pass_schedule(request)` read 정기권 products, the days a pass may start
  on, and the trains it can be bound to. **Buying** a pass is not implemented —
  see below.
- `get_korail_point_summary()` carries the welfare flags (`h_hdcp_flg` and the
  장애인증/보조견 names) that decide whether an account may book 장애 or 안내견
  passenger rows at all.

### The virtual waiting room

`KorailNetFunnelClient` is a standalone client for KORAIL's NetFunnel queue on
`nf.letskorail.com`. It is **off by default** because no live call this
repository has ever made was metered, and it is deliberately unreachable from
`KorailClient` — the API origin guard and the queue origin guard are separate,
and constructing the queue client against a config that has not opted in raises
before any socket exists.

```python
from korail_mobile_api import (
    KorailClient, KorailConfig, KorailNetFunnelClient, inquiry_action,
)

config = KorailConfig(netfunnel_enabled=True)    # explicit opt-in
queue = KorailNetFunnelClient(config)
client = KorailClient(config)

with queue.slot(inquiry_action(peak_season=True)):
    result = client.search_trains(query)
```

Enable it when a queue-shaped failure appears, which is what it was built for.
The handshake and the release are live-confirmed, but the
**queued path is NOT live-exercised**: the server has never actually made this
client wait, so the polling loop, the ttl sleep and the bounds are covered by
offline fixtures only. Treat the handshake as verified and the wait as
built-and-unproven.

## The safety model

This is the part to read before calling anything. It is enforced in code, not by
convention, and the offline suite pins it.

**1. Nothing that changes state moves without an explicit consent object.**
Every one of the fifteen mutation methods starts with
`require_mutation_consent(consent, category)` and raises
`MutationNotAllowedError` before it builds anything. There is no global switch
and no environment variable that turns this off.

**2. Each category is opted into separately.** `MutationConsent` has one flag
per category — `allow_reserve`, `allow_payment`, `allow_cancel`, `allow_refund`,
`allow_discount_card`, `allow_price_recalculation`, `allow_ticket_change` — and
every one defaults to `False`. A consent that authorises a booking cannot cancel
one, and a consent that authorises paying a quoted amount cannot re-price it.

`allow_ticket_change` covers a 여행변경 **and its rollback** on purpose. The
two are one operation: a change that cannot be undone strands an already-paid
ticket half-moved, and the app itself fires the rollback from the screen that
made the change.

**3. `dry_run=True` is the default, and a dry run sends nothing.** With the
default consent, a mutation method validates its inputs and returns a
`MutationPreview` describing the exact form that *would* be posted. The preview's
payload is forced through `redact_payload` on construction, so it can never hold
a raw card number, PNR or other identity even if you built it from real values.

```python
from korail_mobile_api import MutationConsent

preview = client.reserve(train, consent=MutationConsent(allow_reserve=True))
preview.route      # '/classes/com.korail.mobile.certification.TicketReservation'
preview.note       # 'dry-run: not sent'
preview.payload    # redacted; nothing left the process
```

**4. Only `dry_run=False` transmits, and only through one gate.**
`post_mutation_form` is the single method that can reach a mutation route. It
re-checks the consent, refuses a `dry_run=True` consent outright, and asserts
both that the route is a known mutation route and that it belongs to the
category being claimed. The read-only send path refuses every mutation route, so
no read can change state as a side effect.

**This is a consent that would actually book a train:**

```python
hold = client.reserve(
    train,
    consent=MutationConsent(allow_reserve=True, dry_run=False),
)
hold.pnr_no        # a real, unpaid reservation that you now owe a decision

client.cancel_unpaid_hold(
    hold,
    consent=MutationConsent(allow_cancel=True, dry_run=False),
)
```

**5. A card-bearing payment needs one more acknowledgement.** The payment form
carries the PAN in the clear, so `pay_with_fake_card` refuses unless
`fake_card_only=True` and can therefore only ever send a non-chargeable test
card. A real, chargeable card is reachable **only** through the separate
`pay_with_card`, and only on a consent that sets *both*
`real_card_acknowledged=True` and `fake_card_only=False`:

```python
MutationConsent(
    allow_payment=True,
    dry_run=False,
    fake_card_only=False,
    real_card_acknowledged=True,   # a real PAN goes over the wire; money moves
)
```

Both flags default to the safe side, and the transmit gate independently refuses
a payment whose consent claims neither or both — an ambiguous consent is never
sent.

### Error taxonomy

Server-side failures are classified on `h_msg_cd`, the field the app itself
branches on, never on Korean message text. Every type below subclasses the one it
replaces, so an existing `except KorailAppError` still catches everything it used
to, and `code` / `message` / `raw` are present on all of them.

| Exception | Codes | What a caller should do |
| --- | --- | --- |
| `KorailNoResultsError` | `WRG000000`, `P114`, `P100`*, `WRT300005`* | **Nothing was there.** The request was fine. Retry is pointless; ask a different question. |
| `KorailNoDirectTrainError` | `WRD000061` | No *direct* train. Re-ask as a transfer search — which is what the app does. Subclasses `KorailNoResultsError`. |
| `KorailSoldOutError` | `ERR211161` | **Inventory is gone.** Retry is pointless for this train; pick another. |
| `KorailSeatUnavailableError` | `WRI411345`, `ERR911081`, `WRT800176` | The *seat*, not the train. Retrying **without** seat designation may work. |
| `KorailReservationRefusedError` | `WRR800029`, `ERR911531`, `ERR911051` | Reserve refused. Look at what you already hold; `message` carries the server's reason. |
| `KorailInvalidRequestError` | `WRG200018`*, `WRT100002`*, `WRT100124`* | **Fix the payload.** A field was rejected; retry is pointless unchanged. |
| `KorailNotEntitledError` | `ERR299943`* | **This account may not book that fare.** The payload is well-formed; it is refused for who is asking. |
| `KorailServiceUnavailableError` | `SEMGTK` | The back end is down, not your request. |
| `KorailAppUpdateRequiredError` | `SUPDATE` | This client version is refused; no retry interval helps. |
| `KorailAppError` | anything else | Unclassified. `code` and `raw` are intact — this is how the map grows. |
| `KorailSessionExpiredError` | `P058` | **Re-login.** A `KorailAuthError`, deliberately *not* a `KorailAppError`. |
| `KorailDynaPathError` | *(no code — a response header)* | You were flagged, not throttled. Anti-macro rejection carries no `h_msg_cd` at all. |

`classify_app_error` is exported if you want the mapping without the raising.
Codes marked \* are this repository's own live observations rather than APK
branches; which is which, and the one observation deliberately left unclassified,
are in [docs/verification-record.md](docs/verification-record.md).

A warning code attached to a success stays a success — the app dispatches any
unrecognised code on a non-`FAIL` response as a success, and so does this client.

**The library never retries on its own initiative**, and `reserve` in particular
is never retried, because a retried reserve is a duplicate booking.
Classification exists so the *caller* can decide.

## What is proven, and what is only built

Being able to build a request is not the same as knowing the server accepts it.
This distinction is tracked per operation in
[docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md); the short version:

- **Live-verified end to end:** immediate, seat-designated, standby and
  입석+좌석 holds; `confirm_standby_hold`; `cancel_unpaid_hold`; and a
  `pay_with_fake_card` attempt, which the server declined with no charge.
- **Built and never transmitted:** `pay_with_card`, `refund`, `reserve_merge`,
  the whole 할인카드 surface, and `recalculate_price`. Their send paths are
  active code, not blocked code — they have simply never been run.
- **환승 is implemented and NOT live-verified.** `search_transfer_trains` and
  `reserve_transfer` are built from the app's own request builder, but no
  transfer search or hold from this package has ever been sent. Its search side
  is cheap to probe: `get_transfer_stations(dpt, arv)` is a plain read.
  A live transfer hold is not, so do not send one unless you are prepared to
  cancel it in the KORAIL app.

The evidence behind each of those claims — the file:line citations, the codes
each live run returned, and what an operator still has to do — is in
[docs/verification-record.md](docs/verification-record.md).

## What is not implemented, and why

Some of these are boundaries this project chose; some need an entitlement its
account does not have; one was implemented and then removed.

- **Identity-document submission.** The welfare certification routes
  (`certification.disabled.do`, `MeritCert`, `assemblyCert`, `pbep.*`) each
  transmit a 주민등록번호 fragment or a government certificate number and
  *register* an entitlement against the account. Shipping an unverifiable
  identity-document submitter was judged worse than not having one.
- **Password-carrying point routes.** `mlg.lpotAthn.do` and `xPoint.XPointView`
  authenticate with a user-supplied point password and answer with a failure
  counter, so a wrong guess is a state change at the loyalty provider and
  repeated guesses lock the account. They are not reads and are not here. The
  two loyalty routes that *are* reads are.
- **정기권 (commuter pass) purchase — removed on purpose.** It was implemented
  and deleted the same day: a settlement is ₩150,000–₩250,000 with no cancel or
  refund route in this package, and `passPayIssue` is unreachable in the shipped
  app, so there is not even an app capture to compare a form against. The three
  pass *reads* are unaffected. Everything learned about the purchase, and what
  reviving it would cost to prove, is kept in the record.
- **The crew-call submission.**
  `/classes/com.korail.mobile.push.callCrew.do` is the state-changing sibling of
  the crew-request read and remains excluded from the transport allowlist and
  the public client. Reading crew request options never submits a crew call.
- **Anything needing an entitlement this account lacks.** The N카드 reads, and
  the 1~3급 장애 / 안내견 passenger rows, are refused for who is asking rather
  than for how the request is shaped. Proving them needs an account with the
  real-world registration.
- **Check-in, membership mutation, point/mileage mutation, and destructive
  ticket operations.** Not implemented in this version.
- **Authentication bypass, NetFunnel or DynaPath bypass, and general-purpose
  WebView automation.** Out of scope permanently.

## Where the deep material lives

| Document | What is in it |
| --- | --- |
| [docs/verification-record.md](docs/verification-record.md) | The evidence log. Per-feature APK file:line citations, every bounded live run's codes and counts, superseded claims and their corrections. This was the README until 2026-07-26. |
| [docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) | The mutation surface operator-to-operator: what is proven, what each remaining proof would cost, and the trade-offs taken. |
| [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) | Package boundary, route inventory and verification state, as a dated progress log. |
| [docs/api-status-by-service.md](docs/api-status-by-service.md) | All 165 Retrofit entries by service, with each one's live success / failure / unexecuted status. |
| [docs/api-endpoints.md](docs/api-endpoints.md) | The raw endpoint table: method, path, request parameters, return type. |
| [docs/korail-apk-analysis.md](docs/korail-apk-analysis.md) | The APK itself: structure, hosts, login, security, payment, WebView. |
| [docs/deep-dive/README.md](docs/deep-dive/README.md) | Twenty focused subsystem reports and their reading order. |
| [docs/library-build-guide.md](docs/library-build-guide.md) | How the static analysis was turned into this library, and the policy it must keep. |
| [docs/pass-schedule-read.md](docs/pass-schedule-read.md) | The 정기권 schedule read's exact request, typed response, and live-validation boundary. |
| [docs/RELEASE.md](docs/RELEASE.md) | The internal test, build and distribution gate. Not a public release process. |
| [CHANGELOG.md](CHANGELOG.md) | What changed, with the reasoning. |

## Working on this repository

```bash
env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"
```

The offline suite is the gate and it makes no network calls:
`2244 passed, 1 deselected`, where the one deselected test is the explicitly
opted-in live-service test. Live tests run only when `KORAIL_MOBILE_API_LIVE=1`
is set together with credentials you supply yourself; nothing in this repository
ships an account.

Documentation is pinned by the offline suite — principally `tests/test_readme.py`
and `tests/test_release_readiness.py`, with each feature's own module pinning its
own claims. They assert that specific claims, counts and method names still
appear in the document that is supposed to carry them, this file and
`docs/verification-record.md` included. That is deliberate: this repository has
repeatedly caught documentation drifting away from the code, and a claim nobody
checks is a claim nobody can trust.

The APK and the generated decompile directories are not committed. Documentation,
the reproducible inventory output, the client source and the offline contract
tests are.
