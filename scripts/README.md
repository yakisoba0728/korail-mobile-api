# `scripts/` — what these are, and which ones touch the live server

Four scripts are committed here. They are **operator tools, not part of the
package**: nothing under `src/korail_mobile_api/` imports them, and they are not
installed by `pip install`. Run them from a checkout with `python3 scripts/<name>.py`.

Three of the four talk to the real KORAIL server. Read the rule first.

## The rule for every live script here

- **Nothing runs by accident.** Each live script needs the package-wide switch
  `KORAIL_MOBILE_API_LIVE=1` *plus* at least one switch of its own. Setting one
  and not the other runs nothing.
- **Credentials come from the environment only** — never a file, never a
  command-line argument (argv is world-readable through `ps`), never a default.
  A missing one aborts before login. The variables are named in each script's
  own module docstring, which is the authority; this page does not repeat them.
- **Requests are paced** (1.5s minimum spacing by default). KORAIL bans IPs for
  macro-like traffic, and the pacing is installed at the HTTP hook so calls the
  client makes internally are throttled too. Do not lower it.
- **Importing is safe.** Each script performs no I/O, reads no environment
  variable and builds no client at import time; everything happens under
  `main()`. `tests/` asserts this structurally.
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

The one script here that charges a real card. It reserves one adult, pays,
and refunds, on your own account, inside the fee-free refund window. It needs
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
