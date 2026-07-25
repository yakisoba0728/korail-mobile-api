# Mutation Surface — Handoff & Trade-offs

Cross-repo handoff for the consent-gated mutation work on `korail-mobile-api`
and `srt-mobile-api`. It records what is implemented, what was verified against
live servers, what is **not** settled, the trade-offs taken, and how a later
session continues.

Both packages remain **read-only by default**: with no `MutationConsent` (or a
default `dry_run=True` one), the client transmits only login/read requests. A
state-changing request can leave the process only through the dedicated
`post_mutation_form` send gate.

## Status at a glance

| Category | korail | SRT |
|---|---|---|
| reserve | ✅ implemented, **live-verified** | ✅ implemented, live-enabled, **live-verified 2026-07-25** |
| cancel (unpaid hold) | ✅ implemented, **live-verified** | ✅ implemented, live-enabled, **live-verified 2026-07-25** |
| payment | ✅ fake-card-only, **live-verified (declined)** | ⛔ not implemented — route tiered only, not live-enabled |
| refund | ⚠️ implemented, **offline only** (never live-run) | ⛔ not implemented — route tiered only, not live-enabled |

"Live-verified" on both sides means the request was actually sent and its
response observed. korail `refund` is the exception: its send path is fully
active code, NOT blocked, but it has never been run (see item 1 under "NOT
settled"). The SRT reserve/cancel work sits on branch **`feat/srt-cancel` of
`srt-mobile-api`, not merged**.

"Not live-enabled" on the SRT side is a hard gate, not a description of missing
code — see the SRT gate note below.

## Safety model (both repos)

- `MutationConsent` (frozen): per-category `allow_*` (default `False`),
  `dry_run` (default `True`), `fake_card_only` (default `True`).
- `MutationPreview` (frozen): the dry-run result; its `payload` is forced
  through `redact_payload` on construction, so a preview can never hold a raw
  PAN, PNR, or other sensitive identity.
- `post_mutation_form` is the **only** method that transmits to a mutation
  route. It triple-gates: `require_mutation_consent(category)` → refuse
  `dry_run=True` → `assert_mutation_route` (route allowlist) +
  `assert_mutation_route_category` (category/route cross-check). Both repos also
  refuse `category=="payment"` unless `fake_card_only` is set (the PAN is
  transmitted in the clear); on SRT that gate sits behind the category kill
  switch, which refuses payment outright anyway.
- The read-only send path (`post_form`/`get_json` on korail;
  `assert_read_only_request` on SRT) still refuses every mutation route.
- Mutation routes are tracked in a separate `*_MUTATION_ROUTES` set, never added
  to the read-only allowlist.

### SRT-only: the category kill switch

A change on the `fix/mutation-gate-and-docs` branch of `srt-mobile-api` (landed
on that branch, **not merged to its `main`**) adds a fourth gate that SRT has
and korail does not. It was introduced as an empty frozenset and, on the later
`feat/srt-cancel` branch (also **not merged**), now holds exactly:

```python
SRT_LIVE_MUTATION_CATEGORIES: frozenset[str] = frozenset({"reserve", "cancel"})
```

It is asserted in `SrtHttpClient.post_mutation_form` and again at the
`_send_mutation_request` send boundary, so **`payment` and `refund` cannot
transmit at all**, whatever the caller's consent says, while a consented
non-dry-run `reserve` or `cancel` does reach the network. The two were opened
together and only together: reserve creates an unpaid hold and cancel releases
one, so enabling reserve without a transmittable cancel would strand a real
reservation on any mid-flow failure. An SRT test carries a canary pinning that
set to exactly `{"reserve", "cancel"}`, so adding a category fails loudly.

The reason it was needed: `post_mutation_form` was ported from this repo intact
and could transmit any of the four tiered SRT routes, while the "SRT reserve is
preview-only" hardening lived only in `SrtClient.reserve`. `SrtClient.http` is a
public attribute, so a caller could reach the send path directly and bypass the
method-level refusal. The kill switch moves the guarantee from "no method does
this" to "the transport will not do this", which is the claim that actually
holds.

Consequence for the roadmap: enabling a category is an explicit, reviewable edit
to that frozenset, and nothing else in SRT should be described as "live-capable"
until its category is in the set AND a live round trip has been observed. Both
conditions are met for `reserve` and `cancel` (below) and for nothing else.

## SRT — confirmed live facts (2026-07-25)

One operator run of `scripts/verify_reserve_cancel_roundtrip.py` on the
`feat/srt-cancel` branch, against the real server, exited 0. Route: 수서(0551) →
부산(0020), a future date, one adult, general seat, one train. The hold was
cancelled immediately, the ticket list re-read afterwards held no trace of it
(independently re-confirmed in a later session), and it was never paid, so there
was **no charge**. The PNR is deliberately not recorded in either repository.

- **reserve** (`arc/selectListArc05013_n.do`) success envelope:
  `strResult = SUCC`, `msgCd = IRR000018`,
  msg "결제하지 않으면 예약이 취소됩니다.", PNR issued.
- **cancel** (`ard/selectListArd02045_n.do`, body `pnrNo` / `jrnyCnt="1"` /
  `rsvChgTno="0"`) success: `strResult = SUCC`, `msgCd = IRG000000`,
  msg "정상처리되었습니다".
- This is the first confirmation of the cancel wire shape **for SRT's own app
  version**. Until this run it was attested only by the third-party srtgo project
  and had zero hits across all 21,673 files of the v2.0.41 offline decompile —
  which is still true; the run adds live evidence, it does not change the
  bundle. The same applies to reserve's live wiring, now confirmed: SRT's
  NetFunnel `act_10` key flow (the same one train search uses, **not** `act_19`)
  and the referer the client sends were both accepted by the server.
- **Cross-repo observation worth recording: the confirmation codes are identical
  to korail's.** korail's live-verified reserve is also `IRR000018` and its
  cancel `IRG000000` (see the korail section below). Both operators appear to run
  on the same underlying reservation platform, so the code space looks shared.
  That is an observation about two matching pairs of codes, not a proven claim
  about either backend — do not treat korail's other codes (e.g. the payment
  decline `WRT200342`) as predictions for SRT.
- **Scope.** ONE single-journey, one-adult, general-seat round trip. Multi-leg
  (`jrnyCnt` > 1), group and standby reservations were not exercised, so
  `jrnyCnt="1"` is confirmed for the single-journey case only. SRT payment and
  refund were not touched at all.

## korail — confirmed live facts (2026-07-24/25)

Route: 서울(0001) → 부산(0020), a future date. Existing successful credentials
from the gitignored `.env`. Each round trip left reservation history at 0 rows
(no dangling hold) and involved **no charge**.

- **reserve** success envelope: `h_msg_cd = IRR000018`, `strResult = SUCC`.
  The hold response returns the journey count **zero-padded**: `h_jrny_cnt =
  "0001"` (not `"1"`). This broke the first auto-cancel and was fixed
  (`build_unpaid_reservation_cancel_form` now accepts any digit string equal to
  1). This bug was only discoverable live.
- **cancel** (unpaid hold) success: `h_msg_cd = IRG000000`.
- **payment** with an all-zeros fake card: **declined** —
  `strResult = FAIL`, `h_msg_cd = WRT200342`,
  msg "카드번호를 잘못 입력하셨거나, 철도공사에서 결제할 수 없는 카드입니다." No charge.
- The reservation route (`certification.TicketReservation`) is in the DynaPath
  allowlist, so `post_mutation_form` auto-attaches a DynaPath token; the cancel
  and payment routes are not DynaPath routes (no token), matching the app.
- An unpaid hold appears in reservation history with `h_stl_flg=N`
  (unsettled/unpaid), `h_payment_flg=Y` (payment pending).
- Payment amount source: the library sends `hidMnsStlAmt1 =
  hold.received_amount`, the app's `getReceivedAmount()`. The app puts
  `String.valueOf(getReceivedAmount())` into the `PAYMENT_AMOUNT` bundle key
  (`B6/AbstractC1269e.java:406`) and reads it straight back out as
  `hidMnsStlAmt1` (`V4/a.java:27`); `getReceivedAmount()` is computed at
  `PaymentActivity.java:186-199` as the sum of the per-seat `h_rcvd_amt`.
  `h_tot_prc` is display-only — `PaymentActivity.java:174` assigns it to
  `mTotPrc`, whose only reader is `getmTotPrc()` (`:497`), a UI accessor.
  **This entry previously claimed the opposite** ("the library sends
  `hidMnsStlAmt1 = hold.total_price` … which matches the decompiled app
  (`PaymentActivity.java:174`)"). It cited the display assignment as though it
  were the wire value; it was wrong and the code has been corrected.
  The one live payment run never exposed the difference because for a single
  adult in a general seat with no discount the two figures coincide, and the
  card declined at authorization (`WRT200342`) before the amount mattered.
  `hold.received_amount` is parsed from `h_tot_rcvd_amt` when the hold response
  carries it, else summed from the per-seat `h_rcvd_amt` rows; when neither is
  readable the payment builder refuses rather than substituting the display
  total. srtgo uses `h_rsv_amt`; we match the app, which is the authority.

## NOT settled / trade-offs

1. **korail `refund` is not live-verified.** A refund acts on a *settled* ticket
   and needs its original sale window/date/sequence + return password. This
   package's fake-card payment is always declined, so it never produces a paid
   ticket. The refund form + method are wired and offline contract-tested
   against the srtgo/app wire (`ktx.py:1077-1094`), but the live path has never
   run. **Trade-off:** implemented for API completeness; accepted as unverified
   because verifying it would require a real (chargeable) payment.

2. **SRT `payment` and `refund` are still deferred (need live capture) and are
   still kill-switched.** They have no client method, and even a caller reaching
   `SrtClient.http.post_mutation_form` directly cannot send them, because
   `SRT_LIVE_MUTATION_CATEGORIES` holds only reserve and cancel. Their routes are
   tiered (`ata/selectListAta09036_n.do`, `atc/selectListAtc02063_n.do`) and
   srtgo has request wires, but their shapes are **not** in the decompiled
   v2.0.41 bundle and the 2026-07-25 round trip learned nothing about them — it
   never paid the hold it created. Critically, SRT real payment is **not** a
   simple JSON POST like korail — it is a WebView + TransKey (secure keypad) +
   FIDO flow (`ard02017`/`ard02018`), so a clean fake-card JSON attempt is likely
   infeasible. Both still need live response capture to validate parsing.
   *(Resolved for cancel: `ard/selectListArd02045_n.do` is implemented,
   live-enabled and verified — see "SRT — confirmed live facts".)*

3. ~~**SRT `reserve` is preview-only.**~~ **Resolved 2026-07-25.** Ported from
   srtgo `_reserve` (`arc/selectListArc05013_n.do`), it previews by default but
   now transmits under an explicit `dry_run=False` reserve consent, and a live
   reserve creates a real unpaid hold the caller owns. The two uncertainties this
   item listed are settled: the NetFunnel key is the search `act_10` flow and was
   accepted, and the reserve-POST referer (`.../ara/selectListAra10007_n.do`,
   previously a guess inferred from the app flow) was accepted too. Still true as
   written: the deliberate wire divergences `mblPhone` omitted (srtgo sends
   `None`, which `requests` drops) and `runDt1 = departure_date` (mirrors srtgo;
   differs from `run_date` only for a date-shifted train), and the SRT-only guard
   `service_class_code == "17"`. Also unchanged: SRT never retries a failed
   reserve, so at most one hold exists per call.

4. ~~**SRT's hold parser has no defensive fallback, and korail's does.**~~
   **Ported 2026-07-25, before anything could send — as recommended.** korail
   learned this live: a hold exists on the server the moment the POST succeeds,
   so a strict parser that raises on some unrelated malformed field *after* that
   point destroys the PNR and orphans a real reservation. korail has
   `KorailClient._hold_from_reservation_response` (`client.py:1143-1171`); SRT's
   `parse_reservation_hold_response` now has the equivalent — on
   `SrtProtocolError` it returns a minimal hold built from `reservListMap[0]`
   when the raw response still carries a PNR, and re-raises when it does not.
   SRT tightened it in one place korail's version does not cover: a declared
   business FAIL or session expiry is never salvaged, checked both by the
   status classification and again on the raw payload, so the parser cannot
   report a hold for a reservation the server refused. `srt-mobile-api` also
   gained `scripts/recover_hold.py`, which cancels a stranded hold from the PNR
   string alone.

5. **Fake-card enforcement is honor-system on the card value.** The library
   cannot verify a card is non-chargeable; `fake_card_only` is a policy flag
   plus the expectation of a server decline. Real-card mode is refused entirely
   at both the `pay_with_fake_card` method and the `post_mutation_form` gate.

6. **Live-testing risks.** Real unpaid holds (auto-expire, but always
   auto-cancel), anti-bot IP-ban risk, and (SRT) NetFunnel virtual queue. Every
   live run must auto-cancel any created hold and verify reservation history is
   empty afterward.

## How the korail live round trips were run

Session scratchpad scripts (not committed; they read the gitignored `.env` and
print booleans + message codes only, never the PAN/PNR/credentials):

- `live_reserve_cancel.py` — reserve → immediate auto-cancel, with a `finally`
  robust-cancel safety net and a dangling-hold PNR surface on failure.
- `live_payment.py` — reserve → fake-card payment (expect decline) → cancel.
- `recover_hold.py` — diagnose reservation history and cancel any dangling hold
  (used once to clean up the first-attempt orphan before the journey-count fix).

Env: source the repo `.env` (via the scripts' own loader), then
`KORAIL_MOBILE_API_LIVE=1 KORAIL_TEST_DATE=<future YYYYMMDD>`.

SRT went the other way and **committed** its equivalents on `feat/srt-cancel`:
`scripts/verify_reserve_cancel_roundtrip.py` (the round trip, offline-tested
against a mock transport) and `scripts/recover_hold.py` (cancels a stranded hold
from the PNR string alone). The round trip needs two explicit opt-ins,
`SRT_MOBILE_API_LIVE=1` **and** `SRT_LIVE_MUTATION=1`, because "live reads are
acceptable" is not consent to create a reservation. Neither script prints the
password, and the PNR is printed on purpose — an operator who loses it has no way
back to the hold.

## Next-session continuation

- ✅ **DONE — the SRT cancel-then-reserve sequence this section prescribed was
  completed on the `feat/srt-cancel` branch of `srt-mobile-api` (not merged).**
  All five steps were executed in the prescribed order: cancel implemented
  (`Ard02045`, independently re-implemented — not copied from srtgo), korail's
  `_hold_from_reservation_response` fallback ported *before* anything could send,
  `SRT_LIVE_MUTATION_CATEGORIES` opened to `{"reserve", "cancel"}` as a pair
  rather than one at a time (enabling cancel alone was pointless: no hold was
  reachable to cancel, and enabling reserve without cancel would strand one), and
  a live reserve → immediate cancel round trip run once, on 2026-07-25, with an
  auto-cancel `finally` and a PNR banner mirroring korail's. Both halves
  succeeded (`IRR000018` / `IRG000000`) and the NetFunnel/referer uncertainties
  are resolved. See "SRT — confirmed live facts (2026-07-25)".

  The rule the section ended on still stands for every other category: until a
  category is in that frozenset AND a live round trip has been observed, no SRT
  mutation of that category transmits and the docs must not call it live-capable.
- **SRT refund**: unchanged — capture its live response shape
  (`atc/getListAtc14087.do` → `atc/selectListAtc02063_n.do`), then implement the
  method + parser, and only then add the category to
  `SRT_LIVE_MUTATION_CATEGORIES`. Nothing about it was learned on 2026-07-25.
- **SRT payment**: unchanged — investigate the WebView + TransKey + FIDO flow
  (`ard02017`/`ard02018`); decide whether a fake-card attempt is even reachable.
  Note the asymmetry with korail here: korail's fake-card decline is a plain JSON
  POST, SRT's real payment path is not, so korail's payment experience does not
  transfer even though the reserve/cancel codes match.
- **SRT multi-leg / group / standby**: the round trip covered a single-journey,
  one-adult, general-seat hold only. `jrnyCnt` > 1 remains unconfirmed on the
  wire, and `SrtClient.cancel` keeps a `journey_count` override for exactly that
  case.
- **korail refund**: unchanged — only reachable if a real paid ticket is ever
  available (out of normal, no-charge scope).
