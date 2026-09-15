# `scripts/` — what these are, and which ones touch the live server

Seven scripts are committed here. They are **operator tools, not part of the
package**: nothing under `src/korail_mobile_api/` imports them, and they are not
installed by `pip install`. Run them from a checkout with `python3 scripts/<name>.py`.

Six of the seven talk to the real KORAIL server, and two of those charge a real
card. Read the rule first. The three scripts added for the 7.0.6 live check
(the last three sections) meet its switch rule but take credentials differently;
the rule says how.

## The rule for every live script here

- **Nothing runs by accident.** Each live script needs the package-wide switch
  `KORAIL_MOBILE_API_LIVE=1` *plus* at least one switch of its own. Setting one
  and not the other runs nothing.
- **Credentials come from the environment only** — never a file, never a
  command-line argument (argv is world-readable through `ps`), never a default.
  A missing one aborts before login. The variables are named in each script's
  own module docstring, which is the authority; this page does not repeat them.
  The three 7.0.6 scripts prompt for credentials with `getpass` instead. That
  still keeps them out of argv and off disk.
- **Requests are paced** (1.5s minimum spacing by default). KORAIL bans IPs for
  macro-like traffic, and the pacing is installed at the HTTP hook so calls the
  client makes internally are throttled too. Do not lower it.
- **Importing is safe.** Each script performs no I/O, reads no environment
  variable and builds no client at import time; everything happens under
  `main()`. `tests/` asserts this structurally. The three 7.0.6 scripts have the
  same shape, but no test checks them yet.
- **They run against YOUR account.** These exist so a maintainer can check the
  client against the live service once. They are not example code, not a
  scraper, and not something to run on a schedule.

## The scripts

### `verify_distribution.py` — offline, safe

The only one that touches no network and needs no account. It takes a built
wheel and sdist and checks the packaging invariants (metadata, file modes,
nothing forbidden inside). `docs/RELEASE.md` shows where it fits in a release.

### `capture_live_read_surface.py` — live, reads only

Drives the whole read surface once and records the untouched response body for
every call, so the parsers in `src/` can be checked against what the server
actually sends. It logs in once, reuses the session, and derives each argument
from a real previous response. It **never pays and never refunds**: it does not
import `CardPayment` or `PaidTicket`, and the only consent it can build
withholds the money categories. `--reserve` (behind its own extra switch) makes
ONE hold and immediately cancels it.

Its captures contain real personal data. Write them **outside the repository**
— `--out` into a scratch directory, never into a checkout you might commit. The
stdout and the summary are redacted; the raw bodies are not.

### `capture_seat_inventory_evidence.py` — live, reads only

Narrower version of the same idea for the seat-map reads. `docs/verification-record.md`
shows the invocation that produced the evidence recorded there.

### `reserve_pay_refund_roundtrip.py` — live, and it MOVES MONEY

The script here that charges a real card (`retry_delivery_roundtrip.py` below
drives the same run). It reserves one adult, pays, and refunds, on your own
account, inside the fee-free refund window. It needs
three opt-in switches *and* `KORAIL_MAX_FARE`, a ceiling in won: without a
ceiling the run would accept whatever amount the server says is owed, so the
script refuses to start rather than default to unbounded. The ceiling is checked
before the card is read and before any request goes out.

If a run dies partway, it prints the PNR in full and a runnable recovery
command; `--recover` then cancels a stranded unpaid hold, or refunds a paid
ticket after printing the commission. Recovery needs no card ceiling, because
neither branch charges anything.

`--reserve-cancel-only` runs the free half — reserve, then cancel — with no
payment step and no card read at all. Use it to re-verify the reserve and cancel
wire shapes after changing the library: it costs nothing, so it can be repeated,
which the paying run cannot. It still needs the two state-changing opt-ins,
because it does create a real hold, but not `KORAIL_LIVE_REAL_CHARGE` and not
`KORAIL_MAX_FARE` — there is no charge for either to bound.

`docs/MUTATION_HANDOFF.md` documents the flow step by step, including why the
PNR is deliberately *not* masked while the card number is scrubbed from every
line the script writes.

### `verify_706_new_live.py` — live, reads only

Calls the reads connected for 7.0.6 once each: the train calendar, a normal
and a special-schedule (`use_special_schedule=True`) search, and the generic
MaaS menu. `--authenticated` logs in and adds the special search with a
session, delay-discount tickets, product reservations and coupons.
`--special-only` runs the special search alone. `--ticket-maas-history` logs in
and asks for the ticket MaaS menu with a reference taken from the past year's
tickets. It prints the result, the code and the row counts, nothing else.

It needs `KORAIL_MOBILE_API_LIVE=1` and its own `KORAIL_LIVE_706_READS=1`. Only
the modes that log in prompt for the member number and password.

### `retry_unprotected_live.py` — live, reads only

Re-runs reads whose inputs must come from a real earlier response: a V7 read
(`NetworkApi.postSpecificDateData`) and multi-child discount targets, then a
서울 → 부산 search. On its first train it runs the schedule, a merge-seat inquiry
at a real middle station, and a fare quote built from the server's own goods
number. `--post-refund` reads only the reservation history and active tickets.
`--fallback-routes` tries the transfer fallback on two routes with no direct
train. The travel date is fixed in the code at 2026-09-29.

It needs `KORAIL_MOBILE_API_LIVE=1` and its own `KORAIL_LIVE_RETRY_READS=1`, and
always logs in, so it prompts for the member number and password. It prints the
type, the result, the code and the counts.

### `retry_delivery_roundtrip.py` — live, and it MOVES MONEY

Runs the same reserve → pay → refund as `reserve_pay_refund_roundtrip.py` (it
subclasses that script's `RoundTrip`) and adds one read before the refund:
`get_delivery_recipient`, with the paid ticket's original-ticket reference. The
route, time and ceiling are fixed in the code: 서울 → 영등포, 06:00, and
`KORAIL_MAX_FARE=5000`. These override whatever the environment says.

It needs `KORAIL_MOBILE_API_LIVE=1`, `KORAIL_LIVE_MUTATION=1` and
`KORAIL_LIVE_REAL_CHARGE=1`. The member number, password and the four card
values are prompted with `getpass`. It prints through the parent script's
console, so the PNR comes out in full and the card values never do. If the run
fails with a hold or a paid ticket still outstanding, it calls the parent's
recovery straight away.
