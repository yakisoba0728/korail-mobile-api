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
| reserve | ✅ implemented, **live-verified** | ✅ ported, offline dry-run (not live-run) |
| cancel (unpaid hold) | ✅ implemented, **live-verified** | ⛔ route tiered only — deferred |
| payment | ✅ fake-card-only, **live-verified (declined)** | ⛔ route tiered only — deferred |
| refund | ⚠️ implemented, **offline only** (unverifiable) | ⛔ route tiered only — deferred |

## Safety model (both repos)

- `MutationConsent` (frozen): per-category `allow_*` (default `False`),
  `dry_run` (default `True`), `fake_card_only` (default `True`).
- `MutationPreview` (frozen): the dry-run result; its `payload` is forced
  through `redact_payload` on construction, so a preview can never hold a raw
  PAN, PNR, or other sensitive identity.
- `post_mutation_form` is the **only** method that transmits to a mutation
  route. It triple-gates: `require_mutation_consent(category)` → refuse
  `dry_run=True` → `assert_mutation_route` (route allowlist) +
  `assert_mutation_route_category` (category/route cross-check). korail also
  refuses `category=="payment"` unless `fake_card_only` is set (the PAN is
  transmitted in the clear).
- The read-only send path (`post_form`/`get_json` on korail;
  `assert_read_only_request` on SRT) still refuses every mutation route.
- Mutation routes are tracked in a separate `*_MUTATION_ROUTES` set, never added
  to the read-only allowlist.

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
- Payment amount source: the library sends `hidMnsStlAmt1 = hold.total_price`
  (`h_tot_prc`), which matches the decompiled app (`PaymentActivity.java:174`).
  srtgo uses `h_rsv_amt`; we matched the app, which is the authority.

## NOT settled / trade-offs

1. **korail `refund` is not live-verified.** A refund acts on a *settled* ticket
   and needs its original sale window/date/sequence + return password. This
   package's fake-card payment is always declined, so it never produces a paid
   ticket. The refund form + method are wired and offline contract-tested
   against the srtgo/app wire (`ktx.py:1077-1094`), but the live path has never
   run. **Trade-off:** implemented for API completeness; accepted as unverified
   because verifying it would require a real (chargeable) payment.

2. **SRT `cancel`/`payment`/`refund` are deferred (need live capture).** Their
   routes are tiered (`ard/selectListArd02045_n.do`,
   `ata/selectListAta09036_n.do`, `atc/selectListAtc02063_n.do`) and srtgo has
   request wires, but their response shapes are **not** in our decompiled
   v2.0.41 bundle. Critically, SRT real payment is **not** a simple JSON POST
   like korail — it is a WebView + TransKey (secure keypad) + FIDO flow
   (`ard02017`/`ard02018`), so a clean fake-card JSON attempt is likely
   infeasible. cancel/refund need live response capture to validate parsing.

3. **SRT `reserve` is offline only.** Ported from srtgo `_reserve`
   (`arc/selectListArc05013_n.do`), NetFunnel-gated. Not live-run this session
   (would create a real hold; needs a real SRT account). Open uncertainties to
   verify next: NetFunnel-key handling inside the mutation send path, and
   passenger-dict / seat-type fidelity vs srtgo.

4. **Fake-card enforcement is honor-system on the card value.** The library
   cannot verify a card is non-chargeable; `fake_card_only` is a policy flag
   plus the expectation of a server decline. Real-card mode is refused entirely
   at both the `pay_with_fake_card` method and the `post_mutation_form` gate.

5. **Live-testing risks.** Real unpaid holds (auto-expire, but always
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

## Next-session continuation

- **SRT live reserve → cancel** round trip (real account + NetFunnel + auto-cancel
  safety net), mirroring the korail flow, to validate the SRT reserve port and
  resolve the NetFunnel/passenger uncertainties (item 3).
- **SRT cancel/refund**: capture their live response shapes, then implement the
  methods + parsers.
- **SRT payment**: investigate the WebView + TransKey + FIDO flow
  (`ard02017`/`ard02018`); decide whether a fake-card attempt is even reachable.
- **korail refund**: only reachable if a real paid ticket is ever available
  (out of normal, no-charge scope).
