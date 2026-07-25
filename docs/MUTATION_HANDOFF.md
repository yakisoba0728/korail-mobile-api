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
| reserve | ✅ implemented, **live-verified** | ✅ ported, **preview-only**, not live-enabled |
| cancel (unpaid hold) | ✅ implemented, **live-verified** | ⛔ route tiered only — deferred, not live-enabled |
| payment | ✅ fake-card-only, **live-verified (declined)** | ⛔ route tiered only — deferred, not live-enabled |
| refund | ⚠️ implemented, **offline only** (never live-run) | ⛔ route tiered only — deferred, not live-enabled |

korail "live-verified" means the request was actually sent and its response
observed. korail `refund` is the exception: its send path is fully active code,
NOT blocked, but it has never been run (see item 1 under "NOT settled").

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
  `assert_mutation_route_category` (category/route cross-check). korail also
  refuses `category=="payment"` unless `fake_card_only` is set (the PAN is
  transmitted in the clear).
- The read-only send path (`post_form`/`get_json` on korail;
  `assert_read_only_request` on SRT) still refuses every mutation route.
- Mutation routes are tracked in a separate `*_MUTATION_ROUTES` set, never added
  to the read-only allowlist.

### SRT-only: the category kill switch

A change on the `fix/mutation-gate-and-docs` branch of `srt-mobile-api` (landed
on that branch, **not merged to its `main`**) adds a fourth gate that SRT has
and korail does not:

```python
SRT_LIVE_MUTATION_CATEGORIES: frozenset[str] = frozenset()
```

It is asserted in `SrtHttpClient.post_mutation_form` and again at the
`_send_mutation_request` send boundary, so **no SRT mutation category can
transmit at all**, whatever the caller's consent says.

The reason it was needed: `post_mutation_form` was ported from this repo intact
and could transmit any of the four tiered SRT routes, while the "SRT reserve is
preview-only" hardening lived only in `SrtClient.reserve`. `SrtClient.http` is a
public attribute, so a caller could reach the send path directly and bypass the
method-level refusal. The kill switch moves the guarantee from "no method does
this" to "the transport will not do this", which is the claim that actually
holds.

Consequence for the roadmap: enabling a category is now an explicit, reviewable
edit to that frozenset, and nothing else in SRT should be described as
"live-capable" until its category is in the set AND a live round trip has been
observed.

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

2. **SRT `cancel`/`payment`/`refund` are deferred (need live capture) and are
   additionally kill-switched.** They have no client method, and even a caller
   reaching `SrtClient.http.post_mutation_form` directly cannot send them while
   `SRT_LIVE_MUTATION_CATEGORIES` is empty. Their
   routes are tiered (`ard/selectListArd02045_n.do`,
   `ata/selectListAta09036_n.do`, `atc/selectListAtc02063_n.do`) and srtgo has
   request wires, but their response shapes are **not** in our decompiled
   v2.0.41 bundle. Critically, SRT real payment is **not** a simple JSON POST
   like korail — it is a WebView + TransKey (secure keypad) + FIDO flow
   (`ard02017`/`ard02018`), so a clean fake-card JSON attempt is likely
   infeasible. cancel/refund need live response capture to validate parsing.

3. **SRT `reserve` is preview-only.** Ported from srtgo `_reserve`
   (`arc/selectListArc05013_n.do`), the dry-run preview is offline-verified
   (form matches the srtgo wire field-for-field). Live sending (`dry_run=False`)
   is **deliberately refused**: SRT has no callable cancel method to release a
   created hold, and the live NetFunnel-key/referer wiring is unverified — a
   live reserve could strand an uncancellable real hold. The refusal now sits in
   two places: the method-level guard in `SrtClient.reserve`, and the
   `SRT_LIVE_MUTATION_CATEGORIES` gate in the transport, which is what actually
   makes the claim true for a caller who goes around the method. The
   reserve-response parser (`parse_reservation_hold_response` →
   `SrtReservationHold`) is wired for the future live path. Open
   uncertainties to verify before enabling live: NetFunnel-key handling and the
   reserve-POST referer (currently a guess: `.../ara/selectListAra10007_n.do`;
   srtgo sends no explicit referer). Deliberate wire divergences already taken:
   `mblPhone` omitted (srtgo sends `None`, which `requests` drops) and
   `runDt1 = departure_date` (mirrors srtgo; differs from `run_date` only for a
   date-shifted train). SRT-only guard: `service_class_code == "17"`.

4. **SRT's hold parser has no defensive fallback, and korail's does.** korail
   learned this live: a hold exists on the server the moment the POST succeeds,
   so a strict parser that raises on some unrelated malformed field *after* that
   point destroys the PNR and orphans a real reservation. korail therefore has
   `KorailClient._hold_from_reservation_response` (`client.py:1143-1171`), which
   catches `KorailProtocolError`, and — only when the raw response carries a
   non-empty `h_pnr_no` — returns a minimal hold carrying the PNR and journey
   count so the caller can still auto-cancel; with no PNR there is no hold to
   orphan, so it re-raises. SRT's `parse_reservation_hold_response`
   (`parsers.py:643-658`) delegates straight to
   `parse_reservation_attempt_response` and has no such path: any strict-validation
   failure raises and the PNR is lost. That is exactly the orphaned-hold outcome
   the preview-only gate exists to prevent, so the fallback should be ported
   **before** SRT reserve is live-enabled, not after.

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

## Next-session continuation

- **SRT: implement a cancel method FIRST, then enable live reserve.** SRT
  reserve is preview-only precisely because there is no way to release a hold.
  The correct order is:
  1. Implement SRT `cancel` (route `Ard02045`, wire in srtgo `srt.py:1114`).
  2. Port korail's `_hold_from_reservation_response` fallback into SRT's
     reserve path (item 4) so a strict-parse failure cannot lose a PNR that the
     server has already turned into a real hold. Do this **before** anything can
     send, not after the first orphan.
  3. Add `"cancel"` to `SRT_LIVE_MUTATION_CATEGORIES` and live-verify cancel
     against a hold created some other way, if one is reachable.
  4. Remove reserve's method-level `dry_run=False` guard **and** add `"reserve"`
     to `SRT_LIVE_MUTATION_CATEGORIES`. Both are required: with the frozenset
     unchanged the transport still refuses, and that is deliberate — enabling a
     category is meant to be an explicit, reviewable edit.
  5. Run a live reserve → immediate cancel round trip (real account + NetFunnel
     + auto-cancel safety net, mirroring korail) to resolve the
     NetFunnel/referer uncertainties (item 3), then keep it enabled.

  Until step 4 is taken for a given category, no SRT mutation transmits, and the
  docs must not describe SRT as live-capable.
- **SRT cancel/refund**: capture their live response shapes, then implement the
  methods + parsers, and only then add their categories to
  `SRT_LIVE_MUTATION_CATEGORIES`.
- **SRT payment**: investigate the WebView + TransKey + FIDO flow
  (`ard02017`/`ard02018`); decide whether a fake-card attempt is even reachable.
- **korail refund**: only reachable if a real paid ticket is ever available
  (out of normal, no-charge scope).
