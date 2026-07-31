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
| reserve (`1101`, immediate) | ✅ implemented, **live-verified** | ✅ implemented, live-enabled, **live-verified 2026-07-25** |
| reserve (`1103`, seat-designated) | ✅ live-verified 2026-07-26 (seat map honoured) | ⛔ not implemented |
| reserve (`1102`, 예약대기 standby) | ✅ live-verified 2026-07-26 (`IRR000014` on a sold-out train) | ⛔ not implemented |
| standby follow-up (`reservationWait`) | ✅ `confirm_standby_hold`, **live-verified 2026-07-26** (`IRZ000003`) | ⛔ not implemented |
| cancel (unpaid hold) | ✅ implemented, **live-verified** | ✅ implemented, live-enabled, **live-verified 2026-07-25** |
| payment (fake card) | ✅ `pay_with_fake_card`, **live-verified (declined)** | ⛔ not implemented — route tiered only, not live-enabled |
| payment (real card) | ⚠️ `pay_with_card`, explicit opt-in, **never live-run** | ⛔ not implemented — route tiered only, not live-enabled |
| refund | ⚠️ implemented, **never live-run** | ⛔ not implemented — route tiered only, not live-enabled |
| reserve (`1202`, 입석+좌석 — the first half of 병합예약) | ✅ live-verified 2026-07-26 (`IRR000018`, two journeys, 중간연결역 prompt present) | ⛔ not implemented |
| 병합예약 second hold (`reserve_merge`) | ⚠️ implemented, **never live-run** | ⛔ not implemented |
| 정기권 예약/결제 (`pass.passReserve` / `passPayIssue`) | ⛔ **not implemented — implemented once, then removed**; the routes are not on the mutation allowlist and no method can reach them | ⛔ not implemented |
| 운임 재계산 (`certification.PriceReCalculation`) | ⚠️ `recalculate_price`, own `price_recalculation` consent, **never live-run** | ⛔ not implemented |
| 장바구니 담기 (`cart.addCartList`) | ✅ `add_to_cart`, own `cart` consent, live 2026-07-27 (`SUCC`/`IRZ000002`, read back via `get_cart_list`) | ⛔ not implemented |

"Live-verified" on both sides means the request was actually sent and its
response observed. korail `reserve_merge`, `recalculate_price` and the whole
할인카드 surface are the
exceptions: their
send paths are fully active code, NOT blocked, but none has ever been run
(see item 8 under "NOT settled"). The three non-default reservation
job types and `confirm_standby_hold` WERE exceptions until 2026-07-26 and
are not any more; korail `pay_with_card` and `refund` were exceptions until
2026-07-31 and are not any more; the rows above carry the codes each one
returned. The SRT reserve/cancel work sits on branch **`feat/srt-cancel` of
`srt-mobile-api`, not merged**.

"Not live-enabled" on the SRT side is a hard gate, not a description of missing
code — see the SRT gate note below.

## Safety model (both repos)

- `MutationConsent` (frozen): per-category `allow_*` (default `False`),
  `dry_run` (default `True`), `fake_card_only` (default `True`),
  `real_card_acknowledged` (default `False`, korail only).
- `MutationPreview` (frozen): the dry-run result; its `payload` is forced
  through `redact_payload` on construction, so a preview can never hold a raw
  PAN, PNR, or other sensitive identity.
- `post_mutation_form` is the **only** method that transmits to a mutation
  route. It triple-gates: `require_mutation_consent(category)` → refuse
  `dry_run=True` → `assert_mutation_route` (route allowlist) +
  `assert_mutation_route_category` (category/route cross-check). Both repos also
  gate `category=="payment"` on which kind of card the consent claims, because
  the PAN is transmitted in the clear. On korail the consent must state exactly
  ONE of `fake_card_only=True` (a non-chargeable test card, the default) or
  `real_card_acknowledged=True` (an acknowledged real charge); neither is the
  original refusal and both is a contradiction, so an ambiguous consent is never
  sent. On SRT only the `fake_card_only` half exists and it sits behind the
  category kill switch, which refuses payment outright anyway.
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
- **Scope.** Every korail live run above held ONE ADULT in a GENERAL seat on a
  single journey. `KorailClient.reserve` now accepts an arbitrary passenger mix
  and 특실 (item 7 below), and its default still builds exactly the form these
  runs sent — but no other mix and no 특실 request has ever been transmitted.
  Every live run was also `txtJobId="1101"`; the `1102`/`1103` variants (item 8)
  have never been sent.
- **Observed server rule: `ERR299943` 예약할인이 지원되지 않습니다.** On
  2026-07-26, six passenger combinations were accepted live on a 서울→부산 KTX
  and two were refused with this code: 청소년 alone, and 1~3급 장애 + 안내견.
  The forms matched the app exactly, and `ERR299943` has **zero hits anywhere in
  the decompiled APK**, so this is a server-side account-entitlement rule — the
  test account does not carry the 청소년 / 안내견 discount registration — not a
  form defect. Nothing in the package should be "fixed" for it; a different
  account may well be accepted with the identical form.
- **Observed: a hold can carry a warning code and still be real.** One hold came
  back with `h_msg_cd = WRR664296` (senior / 4~6급 장애 discounts do not apply
  at weekends) and was a genuine, cancelable reservation. Success is
  `strResult = SUCC` plus a PNR, **not** `h_msg_cd == IRR000018`; no code path
  in this package treats a non-`IRR000018` code as failure. Standby depends on
  exactly that, since its own success code is `IRR000014`.

## NOT settled / trade-offs

1. **korail `pay_with_card` and `refund` are live-verified as of 2026-07-31, for
   one narrow case.** A refund acts on a *settled* ticket and needs its original
   sale window/date/sequence + return password. The fake-card payment is always
   declined, so it never produces a paid ticket; only a real charge does. On
   2026-07-31 `scripts/reserve_pay_refund_roundtrip.py` drove the whole loop with
   a real card: 서울→광명, 2026-08-31, 8,400 KRW, one adult, general seat.
   Payment answered `SUCC`/`IRT000000` "정상발매처리,정상발권처리";
   `CommissionView` quoted 8,400 KRW back with a 0 KRW fee; the refund answered
   `SUCC`/`IRT200277` "반환이 정상 처리되었습니다"; reservation history was empty
   before and after. **What that does NOT settle:** instalments, corporate cards,
   more than one passenger, more than one journey, partial refunds, and any
   refund close enough to departure that a fee applies. The run also surfaced
   three padded wire shapes the offline fixtures had guessed wrong — see
   verification-record.md. **Trade-off:** the surface stays consent-gated and
   dry-run-by-default; one successful round trip is evidence for that one shape,
   not a licence to assume the rest.

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

5. **Card-kind enforcement is honor-system on the card value.** The library
   cannot verify whether a card is chargeable; `fake_card_only` and
   `real_card_acknowledged` are policy claims the caller makes, not facts the
   library can check. What the gates do enforce is that the claim is stated and
   unambiguous: `pay_with_fake_card` accepts only the fake-card claim, the
   separate `pay_with_card` accepts only the acknowledged-real-charge claim, and
   `post_mutation_form` refuses a payment consent that makes neither claim or
   both.

6. **Live-testing risks.** Real unpaid holds (auto-expire, but always
   auto-cancel), anti-bot IP-ban risk, and (SRT) NetFunnel virtual queue. Every
   live run must auto-cancel any created hold and verify reservation history is
   empty afterward.

7. **korail multi-passenger and 특실 holds are LIVE-VERIFIED (2026-07-26).**
   `KorailClient.reserve` takes a `KorailPassengerCounts` (어른, 청소년,
   어린이, 동반유아, 경로, 1~3급 장애, 4~6급 장애, 안내견) and a
   `KorailSeatClass` (일반실 / 특실), both keyword-only and defaulted to one
   adult in a general seat, so the default request stays byte-for-byte the one
   the 2026-07-24/25 runs sent. Three reserve->cancel round trips on
   서울->부산 20260809 train 075 confirmed the wire shapes, each cancelled
   immediately (`SUCC`/`IRG000000`) with the account verified empty afterwards:
   - two adults, general: hold total `119,600` = 2 x `59,800`, so the count
     reaches the server rather than being ignored.
   - one adult, 특실: reading the hold back with
     `get_ticket_reservation_detail` returned `h_psrm_cl_nm='특실'`,
     `h_srcar_no=13`, `h_rcvd_amt=83,700` — the cabin code is honoured.
   - **The 특실 hold is what proves the payment-amount fix mattered.** Its
     `h_tot_prc` is `59,800` (the general fare) while `h_tot_rcvd_amt` is
     `83,700`. `build_card_payment_form` sends `hidMnsStlAmt1=83,700`. Had the
     builder still used `h_tot_prc`, a 특실 payment would have underpaid by
     23,900 KRW. The one-adult general round trip could not have shown this:
     there the two values coincide.
   Static evidence behind the shapes: `w4/a.java:49-73` (the eight rows and
   their fixed type/discount codes), `m5/c.java:330` (`txtTotPsgCnt` is the sum
   of all eight — 동반유아 and 안내견 included), `m5/d.java:32-33` (maximum 9),
   `c5/b.java:72` + `U4/a.java:88` + `K4/o.java:7-8` (`txtPsrmClCd1`).
   Still unverified: every passenger type other than 어른, any mix of types,
   and every error envelope. **Trade-off:** the mix is validated only as far as
   the app's picker validates it (non-negative, at least one, at most nine);
   two picker warnings with no wire representation
   — a 동반유아 needs an adult-ish companion (`m5/c.java:452-455`) and an
   안내견 needs more 장애 passengers than dogs (`m5/c.java:458-465`) — are
   documented but deliberately not enforced, since guessing at the server's
   version of them would reject mixes it may accept. An operator verifying this
   should reserve→cancel (no payment) only the combinations they actually
   intend to use; nothing here generalises from one mix to another.

8a. **2026-07-26: both variants are now live-verified.**

   *Seat designation (`1103`).* Two adults on 서울->부산 20260809, requesting
   car 11 `seat_no` `37` and `33`. The reservation read back as car 11 seats
   `10A` and `9A` — **the seats requested**. The apparent mismatch in the first
   attempt was a false alarm: an inventory record carries BOTH identifiers,
   `{"seat_no": "45", "seat_spec": "12A"}`, where `seat_no` is what the
   reservation form sends and `seat_spec` is the printed label the reservation
   detail echoes back. `seat_no` 37 is label `10A` and 33 is `9A`, so the server
   honoured the `OSrcar` map exactly. Cancelled `IRG000000`, account empty.
   **Anyone comparing requested against booked seats must compare `seat_spec`
   to `h_seat_no`, not `seat_no` to `h_seat_no`.**

   *Standby (`1102`).* Verified against a genuinely sold-out train: 서울->부산
   20260731 16:00 had every train at `h_gen_rsv_cd="13"`, and train 125 carried
   `h_wait_rsv_flg=" 9"`. One adult, general class:
   - reserve -> `SUCC` / `IRR000014` "예약대기 가능합니다." — the code the APK
     predicted (`ui/inquiry/rir/orr/a.java:222-225`).
   - `confirm_standby_hold` -> `SUCC` / `IRZ000003` "정상적으로 수정 되었습니다."
     (both options off, so no phone number was transmitted).
   - cancel -> `IRG000000`, account empty.
   The flag values observed live match the APK exactly: `" 9"` standby-eligible
   (leading space is real), `" 0"` sold out without standby, `"-2"` seats
   available. korail2's `-2`/`9`/`0` claim is right about the meanings but wrong
   about the wire format — the values are space-padded to width 2.

8b. **A stale session reads as an auth failure, not as a session expiry.**
   After a long run, `get_seat_inventory` began answering
   `[3]인증정보에 문제가 있습니다.` and kept doing so. It was first read as rate
   limiting; it was not. A fresh `login()` cleared it immediately. Treat that
   message as "re-login", and note it does NOT arrive as `P058`, so the existing
   session-expiry path does not catch it.

8c. **Design record for `1103` / `1102`** (was: NOT
   live-verified.** Both are reachable from `KorailClient.reserve` through the
   keyword-only, defaulted `job_type` (`KorailReservationJobType`), and standby
   has a second, separately gated call. Every byte of both forms comes from the
   APK; **nothing in this repository has transmitted either one.**

   *Seat designation (`1103`).* The app switches the job id in the same three
   lines that install the `OSrcar` map (`C5/a.java:143-146`), and clears that
   map whenever it rebuilds an ordinary journey (`C5/a.java:118`). `OSrcar`
   reaches Retrofit as the last `@FieldMap` of the call
   (`CertificationService.java:52-54`), so an empty map contributes **no fields
   at all** — a `1101` hold carries no `txtSrcarCnt`, and srtgo's unconditional
   `txtSrcarCnt="0"` is a shape the app never sends. The keys, from
   `OSrcar.java:6-30` + `SeatSearchActivity.java:675-683`: `txtSrcarCnt` (the
   **seat** count, `selectedSeatList.size()`), then `txtSrcarNo{i}` /
   `txtSeatNo{i}` with `i` from **1**. The car number is
   `SeatSearchRequest.getTxtSrcarNo()` (`:269-271`) and the seat is
   `Seat.getSeat_no()`, i.e. exactly `SeatCar.car_no` / `SeatInventoryResponse.car_no`
   and `PhysicalSeat.seat_no` from this package's own seat reads —
   `KorailSeatAssignment.from_inventory()` pairs them. The seat count must equal
   `txtTotPsgCnt`, which is the app's own rule (`SeatSearchActivity.java:902`
   enables 선택완료 only while `selectedSeatCount == G0()`, and `G0()` at
   `:273-278` is `txtTotPsgCnt`); a mismatch is refused before anything is
   built, since a partial seat list is how a half-booked hold happens.

   *Standby (`1102`).* Job id at `DirectInquiryActivity.java:434`. Eligibility
   is **not** "sold out": `U4.a.b()` — which jadx cannot decompile, so read
   `analysis/apktool/smali/U4/a.smali:1250-1290` and `:1969-1981` — sets the
   train row's `wait` bundle flag from
   `N.isNotNull(h_wait_rsv_flg) && " 9".equals(h_wait_rsv_flg) && cVar == RSV_DEFAULT`,
   ANDed with the standard-cabin branch. That bundle flag is the only input to
   `a5/k.java:120-126`'s `G0()`, which with a 일반실 tab is the only thing that
   enables the 예약대기 button (`a5/u.java:371` → `:401`). `h_gen_rsv_cd` is
   never consulted. So the wire literal is `" 9"` — a leading **space**, then a
   9 — exported as `KORAIL_STANDBY_WAIT_FLAG`. korail2 (`korail2.py:196-199`)
   describes the field as `-2` / `9` / `0`; only the 9 has any support in this
   app and its spelling is right-aligned in two characters. Because a standby
   train is normally 매진, `reserve` skips the "seats available" check for
   `1102`, requires the flag plus 일반실 (there is no 특실 standby), and
   computes `txtStndFlg` from `S4/J.java:83-84`'s `isStndSeat` instead of
   pinning `"N"`.

   *Standby is members-only, and that is real.*
   `ReservationRequest.java:105-119`'s `isNonmemberNotEnable()` returns true for
   `jobId == "1102"`, and its only caller, `BaseActivity.java:350`, passes the
   negation to `moveToLogin` as "may this request be retried as a non-member".
   A 비회원 therefore can never place a standby booking. This package satisfies
   it structurally — every mutation needs a logged-in member session and
   `nonMember.NonMemTicket` is not in any allowlist — and the form carries none
   of the non-member identity fields.

   *The follow-up call.* A standby hold returns `h_msg_cd = IRR000014`
   (`KORAIL_STANDBY_HOLD_MESSAGE_CODE`), the only code that opens 예약대기
   screen (`ui/inquiry/rir/orr/a.java:222-225`). That screen POSTs
   `reservationWait.ReservationWait` (`ReservationWaitService.java:10-12`) with
   `txtPnrNo`, `txtPsrmClChgFlg`, `txtSmsSndFlg` and `txtCpNo` —
   `ReservationWaitActivity.java:147-155, 213-228`. `txtCpNo` is set **only**
   when the SMS box is checked (otherwise the getter is null and Retrofit drops
   the field), and the app refuses fewer than 10 digits against 3+4+4-digit
   inputs (`res/values/integers.xml:34-35`), so this package sends 10 or 11
   digits or omits the key. `confirm_standby_hold` is that POST.

   **Trade-off: it is a `"reserve"`-category mutation, not a new category.**
   It changes no money and releases no seat; it completes the booking an
   `allow_reserve` consent already authorised, on a PNR that same consent just
   created. A new category would mean a caller who opted into placing a standby
   booking could not finish placing it — and every `MutationConsent` written
   before today would silently deny an operation it plainly intended to allow.
   That is not a safety boundary, it is a footgun. The route/category
   cross-check still stops a reserve consent from reaching payment, cancel or
   refund, and the call still goes through `post_mutation_form` like every other
   mutation — never the read path.

   **How an operator live-verifies these.** Both need reserve→cancel only; no
   payment.
   - `1103`: pick a train with seats, `get_seat_cars` → `get_seat_inventory` →
     build `KorailSeatAssignment`s → `reserve(..., job_type=SEAT_DESIGNATED,
     seats=[...])` with `dry_run=False`, then read the hold back with
     `get_ticket_reservation_detail` and check `h_srcar_no` / `h_seat_no` are
     the seats that were asked for — that is the only thing that proves the
     `OSrcar` keys reached the server rather than being ignored — then
     `cancel_unpaid_hold`. Worth doing once with **two** passengers, because a
     single seat cannot distinguish "the index is 1-based" from "the server
     ignored the map".
   - `1102`: find a **sold-out** 서울→부산 KTX and check its
     `TrainSummary.wait_reservation_flag` is `" 9"` first (a dry-run `reserve`
     with `job_type=STANDBY` will say so without sending anything). Then
     `dry_run=False`, expect `strResult=SUCC` with `h_msg_cd=IRR000014`, call
     `confirm_standby_hold` (start with both options off, so no phone number
     leaves the machine), and `cancel_unpaid_hold` the PNR. Record what
     `h_msg_cd` the follow-up returns — it is completely unknown.
   - Unknowns worth recording either way: whether `1103` accepts seats spread
     across two cars (the app's UI can only ever select within one car, though
     the wire format is per-seat), and what the server says when a designated
     seat has been taken between the inventory read and the hold.

9. **korail `recalculate_price` (운임 재계산) has never been sent.** The wire
   shape is settled from the APK and needs no further static work: the six
   `List` `@Field`s are index-aligned one row per seat (`a6/C1042B.java:275-283`,
   confirmed in `smali/a6.1/B.smali`), and Retrofit emits them as repeated keys
   rather than indexed ones (`RequestBuilder.smali:1537-1601`). What is unknown
   is entirely server-side.

   *Cost to prove: one hold, and no money, if it is done in this order.* Place
   an ordinary `1101` hold (₩0 until settled), read it back with
   `get_ticket_reservation_detail` to get each seat's `h_psg_tp_cd`,
   `h_psrm_cl_cd` and `h_dcnt_knd_cd1`, build one `PriceRecalculationRow` per
   seat **echoing those values unchanged and applying no discount** (all three
   discount fields `""`), and call `recalculate_price` with
   `dry_run=False`. That is the identity case: it should return the hold
   re-priced to the amount it already had. Compare `received_amount` against
   the same field from the hold. Then `cancel_unpaid_hold`. Nothing is
   settled at any point, so the run costs nothing but the hold.

   Only after the identity case answers should a real discount be applied, and
   then only one whose entitlement the account actually has. **Do not run this
   against a hold anyone intends to pay for**, and do not run it against a
   settled ticket at all: a wrong row changes what the passenger is about to be
   charged, which is the whole reason it has its own consent category.

   *Unknowns worth recording:* whether the server validates `txtPsgGridcnt`
   against the PNR or trusts it; what it does when `dcnt_knd_cd1` disagrees
   with the hold's stored discount; whether it rejects or silently ignores a
   discount the account is not entitled to; and whether the response's
   `h_tot_rcvd_amt` is the re-priced amount or the original one. Also worth
   confirming that the repeated-key encoding is accepted at all — that is the
   single assumption a live call would most usefully falsify, and a
   `strResult=FAIL` with a parameter-count message would say so immediately.

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

## The real-card round trip (`scripts/reserve_pay_refund_roundtrip.py`)

This one IS committed, because it is the only way `pay_with_card` and `refund`
can ever stop being unverified. It reserves one adult on the configured route
about two weeks out, pays with a real card, and refunds — printing what it is
about to do at every step.

Four things must be set, none of them enough alone:

| variable | meaning |
|---|---|
| `KORAIL_MOBILE_API_LIVE=1` | may touch the live server |
| `KORAIL_LIVE_MUTATION=1` | may change state |
| `KORAIL_LIVE_REAL_CHARGE=1` | may charge a REAL card |
| `KORAIL_MAX_FARE=<won>` | the ceiling on what may be charged |

The card is read from `KORAIL_CARD_NUMBER`, `KORAIL_CARD_PASSWORD` (first two
PIN digits), `KORAIL_CARD_EXPIRE` (YYMM) and `KORAIL_CARD_BIRTHDAY` (YYMMDD) —
environment only, never a file and never a command-line argument, because argv
is world-readable through `ps`. `KORAIL_MAX_FARE` is a ceiling in won and is
**required** on the charging path (it used to be optional; a run without it had
no ceiling at all, which is not a defensible default for a script that charges a
real card). It is checked before the card is read, before login and before any
request; if the server later says more is owed than the ceiling, the run stops
and releases the unpaid hold. `--recover` does not need it, because neither of
its branches charges anything. `KORAIL_TRAIN_NO` pins an exact train.

```bash
KORAIL_MOBILE_API_LIVE=1 KORAIL_LIVE_MUTATION=1 KORAIL_LIVE_REAL_CHARGE=1 \
KORAIL_MAX_FARE=20000 \
python3 scripts/reserve_pay_refund_roundtrip.py
```

The PAN, the card password, the expiry and the birthday are scrubbed from every
line it prints, including exception text, by exact-value substitution of the
four values it was handed. It applies no generic digit-run pattern, because a
KORAIL PNR is 15 decimal digits and is therefore indistinguishable from a PAN by
shape: on 2026-07-25 a live run printed `LIVE HOLD CREATED   PNR
[REDACTED_CARD]`, and the same for the recovery command line, leaving a real
unpaid hold with no identifier. The PNR is printed unredacted on
purpose, the instant the hold exists, and again in a banner with a runnable
recovery command if anything later fails — a paid ticket whose PNR the operator
does not know is the worst outcome the script can produce. That recovery command
is the script's own `--recover` mode, driven by `KORAIL_RECOVER_PNR`: it cancels
an unpaid hold, or prints the commission and refunds a paid ticket. It does NOT
need `KORAIL_LIVE_REAL_CHARGE`, because neither branch charges anything.

Caveat carried over from item 1: a live ScheduleView row supplies no goods
number, so `trn.prcFare.do` usually cannot be built and "cheapest" cannot be
established from a fare QUOTE. The script never invents a train-class price
ranking. It picks, in order: the train named by `KORAIL_TRAIN_NO` (verified to
select that exact train, and to abort before reserving when it is not among the
reservable ones); else the cheapest by fare quote; else the cheapest by the
search row's own `h_rcvd_amt`/`h_rcvd_fare`, which
`RsvInquiryResponse.TrainInfo` declares (`:102-104`) — printed as
`~N KRW (HINT from the search row, not a quote)` and never as a fare, because it
is not what the payment will settle; else the first reservable train, saying
plainly that cheapest could not be established. Whichever branch runs, the
printed reason names it, the authoritative amount is still read back and
cross-checked at step (d) before any money moves, and `KORAIL_MAX_FARE` is the
only thing that caps the charge — which is exactly why the script now refuses to
run without it.

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
- **korail 병합예약** (branch `feat/merge-and-pass`, not merged): the cheap half
  is free. Search any busy corridor and look for a row whose
  `merge_seat_application_flag` is `A` or `G` (일반실); that alone tells you the
  app would show 입석+좌석 예매. Then `reserve(..., job_type=MERGE_STANDING)`
  creates a real unpaid 입석 PNR — cancel it immediately with
  `cancel_unpaid_hold`, which does work for it (one journey). The claim to check
  on that reply is whether its `h_msg_mndry`/`h_msg_txt5` contains the literal
  `<중간연결역 변경>`: that is how the app learns a merge is on offer, and it is
  the one link in the chain that no static reading can confirm. Then
  `get_merge_seats_inquiry` (free) should answer with a `midStnList` and two
  `trn_info` rows sharing one `h_trn_no`. `reserve_merge` last, and cancel it
  too. Also open: whether KORAIL validates `arvTm_1`, which the app leaves at the
  whole route's arrival time rather than leg 1's.
- **korail 정기권: there is nothing for an operator to run, and that is the
  answer, not an omission.** The purchase pair was implemented and then removed;
  no method, route registration or consent category for it survives, so no
  amount of consent can send `passReserve` or `passPayIssue` from this package.
  The reasoning, in operator terms: the settlement is roughly ₩150,000–₩250,000
  for a 1개월 pass with **no refund path and no cancel route here**, and the
  shipped app cannot issue `passPayIssue` either — its `isCommPaymentRequest()`
  tests the *response* class where a *request* is required, so the branch is
  always false — which means there is no app capture to compare a live attempt
  against. An operator would be paying, unrecoverably, to learn whether a form
  nobody has ever sent is accepted. Everything that was established about both
  calls is written down in README's 정기권 section, including the one step that
  would actually be worth its cost if this is ever revived (capturing a real
  `passReserve` `main_info`, which IS the payment's first `@FieldMap`).
