# KORAIL Next Safe Reads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add faithful typed support for the next seven caller-closed KORAIL reads, plus offline-only typed contracts for the two routes whose live prerequisites are not closed.

**Architecture:** Extend the existing frozen model / exact payload / strict parser pattern. Add a narrowly scoped ordered-form path for alternative and repeated Retrofit fields; keep arbitrary mappings impossible. Public client transport is added only for R13, R17, R31, R32, R43, R45, and R52. R39 and R54 receive synthetic-fixture-backed models/parsers but remain absent from `KorailClient` and `KORAIL_READ_ONLY_ROUTES`.

**Tech Stack:** Python 3.11+, frozen dataclasses, `httpx`, `pytest`, existing KORAIL safety and DynaPath layers.

## Global Constraints

- Work only on `codex/raw-completion` or an isolated branch/worktree based on commit `6aa05d07226ed4594cbe24bd0595538961e320a3`; never implement directly on `main`.
- Use TDD for every behavior change: add a failing focused test, run it and record the expected failure, then add the minimum implementation.
- Do not access `.env`, credentials, secure raw-capture directories, or the network. All fixtures must be synthetic.
- Do not add reservation, seat hold/selection, payment, ticketing, cancellation/refund, check-in, member mutation, points mutation, native bridge, or external seat-map behavior.
- Do not expose a free-form `Mapping`, `FieldMap`, extra request fields, guessed discriminator, alternate path, retry, fallback, queue bypass, or synthetic NetFunnel token.
- Require the full response envelope and exact `strResult="SUCC"`; preserve existing `P058`, `FAIL`, and `WRC000288` typed errors and session clearing.
- Preserve modeled unknown response data only in `raw` fields with `repr=False`. Customer, ticket, PNR, reservation, URL, name, birth-date, and free-text fields must not appear in `repr`.
- Request validation must finish before DynaPath generation and transport.
- DynaPath remains enabled only where already evidenced: R52. It is forced off for every other new public read. Do not change `DYNAPATH_ALLOWLIST_PATHS`.
- The live inventory remains `165 = 28 success + 9 failure + 128 unexecuted` until a separately reviewed bounded live run provides new evidence.
- After both tasks, the exact transport boundary must be `45` routes and the public client surface `48` methods. R39 and R54 do not contribute to either count.

---

### Task 1: Fixed and account-shaped reads

Implement R13, R32, R43, and R45 as public reads. Add R54 response parsing only and explicitly prove that transport remains unavailable.

**Files:**

- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/session.py`
- Modify: `src/korail_mobile_api/http.py`
- Modify: `src/korail_mobile_api/safety.py`
- Modify: `src/korail_mobile_api/read_models.py`
- Modify: `src/korail_mobile_api/read_payloads.py`
- Modify: `src/korail_mobile_api/read_parsers.py`
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Create: `tests/test_next_account_reads.py`
- Create: `tests/fixtures/mchd_discount_targets_success.json`
- Create: `tests/fixtures/customer_trip_info_success.json`
- Create: `tests/fixtures/maas_service_detail_list_success.json`
- Create: `tests/fixtures/trip_change_dates_success.json`
- Create: `tests/fixtures/tour_train_info_success.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/NEXT_SESSION.md`
- Modify: `tests/test_readme.py`

**Interfaces:**

- `KorailSession.customer_no: str | None`, appended with `repr=False`, populated only from login `strCustNo`.
- `KorailClient.get_multi_child_discount_targets(departure_date: str) -> MultiChildDiscountTargetResponse`.
- `KorailClient.get_customer_trip_info() -> CustomerTripInfoResponse`, using session `customer_no`, fixed `medDvCd="03"`, and fixed `regSqno="0"`.
- `MaasServiceDetailQuery.current()` emits only `Device`, `Version`; `MaasServiceDetailQuery.history(start_date, end_date)` emits both dates after them.
- `KorailClient.get_maas_service_details(query: MaasServiceDetailQuery | None = None) -> MaasServiceDetailListResponse`; `None` is the no-date current shape.
- `KorailClient.get_trip_change_dates(departure_date: str) -> TripChangeDateResponse`.
- `parse_tour_train_info_response(raw) -> TourTrainInfoResponse` is internal/static-contract support only. There is no `KorailClient.get_tour_train_info`, no R54 safety entry, and no raw-string request builder.

**Exact response fields:**

- R13 row strings: `btdt`, `custFmlyNm`, `dcntKndCd`, `fmlySqno`, `psgTpCd`, `psgTpNm`, `psrmClCd`, `rqDcntKndCd`.
- R32 row strings: `addSeatAttCd`, `adltHdcpPrnb`, `adulCnt`, `arvStnCd`, `arvStnNm`, `babyAcpnPrnb`, `chgDttm`, `chgUsrId`, `chilCnt`, `chldHdcpPrnb`, `custMgNo`, `dayCd`, `dirSeatAttGpCd`, `dirtChtnDvCd`, `dptStnCd`, `dptStnNm`, `ectbTrnDptTm`, `edrPrnb`, `inclFlg`, `jobStHr`, `locSeatAttGpCd`, `medDvCd`, `psrmClCd`, `ptwtTtl`, `regDttm`, `regSqno`, `regUsrId`, `tripDno`, `trnClsfCd`, `trnCnecFlg`, `trnGpCd`, `utlDno`.
- R43 row strings: `addSrvDvCd`, `addSrvGdCd`, `addSrvId`, `addSrvMrkEntId`, `addSrvMrkEntNm`, `addSrvNm`, `addSrvPrgSttCd`, `addSrvReqNo`, `cgPsRefAtclCont`, `coptEntRsvNo`, `dlivPsbClsTm`, `dlivPsbStTm`, `leadMsgCont1`, `leadMsgCont2`, `pnrNo`, `reqDt`, `reqQnty`, `rsvSpecUrl`, `utlClsDt`, `utlStDt`.
- R45 optional strings: `lastRunDt`, `tripChgDate`; optional/null list `tripChgDates` normalizes to a tuple.
- R54 shape: `seat_infos.seat_info[].h_seat_att_cd`, nested `seat_add_infos.seat_add_info[].h_psg_num` where the passenger count is a JSON integer and never bool/float/string.

- [ ] **Step 1: Write failing route, payload, session, parser, repr, and holdback tests**

  Add focused tests that assert exact bodies in this order:

  ```text
  R13: Device, Version, Key, dptDt
  R32: Device, Version, Key, custMgNo, medDvCd, regSqno
  R43 current: Device, Version
  R43 history: Device, Version, qryDtFrom, qryDtTo
  R45: Device, Version, Key, tripChgDate
  ```

  Assert session guards for R13/R32/R43/R45; R32 must fail before transport if `strCustNo` is absent and must never substitute member/member-card numbers. Assert both R43 dates or neither, ASCII `YYYYMMDD`, ordered range, and at most three calendar months. Assert R54 has parser coverage but no client method or safety route. Cover exact `SUCC`, `SUCCESS` rejection, `P058`, `FAIL`, malformed containers/rows/scalars, nullable containers, repr hiding, no DynaPath invocation, and validation-before-transport.

- [ ] **Step 2: Run the focused file and verify RED**

  Run:

  ```bash
  PYTHONPATH="$PWD/src" pytest -q tests/test_next_account_reads.py tests/test_session.py tests/test_http.py tests/test_public_contract.py tests/test_readme.py
  ```

  Expected: collection/import or assertion failures for the new types, methods, routes, parsers, and customer-number extraction; no network access.

- [ ] **Step 3: Implement the minimum frozen models, exact builders, strict parsers, session extraction, routes, and methods**

  Add only four new exact routes. Extend safety with exact ordered variants without weakening existing route checks. All public methods must call one exact endpoint once, without adjacent requests. `get_maas_service_details` must call `include_common=False` so `Key` is absent. Force `include_dynapath=False` on all four.

- [ ] **Step 4: Run focused GREEN, then regression tests**

  Run the command from Step 2 until it passes, then:

  ```bash
  PYTHONPATH="$PWD/src" pytest -q -m "not live"
  python3 -m compileall -q src tests
  git diff --check
  ```

  Expected: all commands succeed; safety/public counts become `42` routes and `45` methods at the end of this task.

- [ ] **Step 5: Document static-only support and commit**

  Document exact routes, session policy, no-live evidence, R54 holdback, unchanged runtime inventory, and no mutation expansion. Commit all Task 1 files with:

  ```bash
  git commit -m "feat: add fixed account read contracts"
  ```

---

### Task 2: Tagged variants, ordered repeated forms, and fare quote

Implement R17, R31, and R52 as public reads. Add R39 request/response models and parser tests only, while keeping its NetFunnel-gated transport unavailable.

**Files:**

- Modify: `src/korail_mobile_api/http.py`
- Modify: `src/korail_mobile_api/safety.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/read_models.py`
- Modify: `src/korail_mobile_api/read_payloads.py`
- Modify: `src/korail_mobile_api/read_parsers.py`
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Create: `tests/test_next_variant_reads.py`
- Create: `tests/fixtures/gifticket_list_success.json`
- Create: `tests/fixtures/cmtr_info_success.json`
- Create: `tests/fixtures/price_2_fare_success.json`
- Create: `tests/fixtures/product_train_inquiry_success.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/NEXT_SESSION.md`
- Modify: `tests/test_readme.py`
- Modify: existing safety/public-contract tests that assert exact route/method counts.

**Interfaces:**

- `GiftTicketHistoryRequest.sent(start_date, end_date)` fixes `qryDvCd="A"`, `qryVal="E"`, and emits blank `usePsbFlg`.
- `GiftTicketHistoryRequest.received(start_date, end_date)` fixes `qryDvCd="C"`, `qryVal="E"`, and emits blank `usePsbFlg`.
- `GiftTicketPaymentEligibilityRequest()` fixes `qryDvCd="F"`, `qryVal="E"` and omits dates, `usePsbFlg`, and all continuation fields.
- `KorailClient.get_gift_ticket_list(request) -> GiftTicketListResponse`; session required, no DynaPath, one request, no 404 fallback/retry.
- Three frozen R31 request variants represent job `a`, `b`, and `c`. Job codes are internal constants, not public string parameters. Job `b` preserves grouped repeated `cmtrUtlAgeCd` followed by grouped repeated `psgPrnb`; lengths and `psgCnt` match. Job `c` accepts an immutable repr-hidden original-ticket reference and inquiry type `"0"` or `"1"`.
- `KorailClient.get_commuter_info(request) -> CommuterInfoResponse`; session is mandatory for job `c`, and may be conservatively mandatory for the whole public wrapper if one uniform boundary is simpler.
- `PriceFareLeg` contains exactly departure station, arrival station, run date, train number, goods number, requested seat attribute, train group, and standing train class. It exposes no raw mapping and rejects comma-bearing components.
- `PriceFareQuoteRequest` accepts exactly one or two legs plus `TrainSearchMetadata` with a nonempty server-provided `menu_id`; it derives `chtnDvCd` and intentionally never emits `trnCnt`.
- `KorailClient.get_price_fare_quote(request) -> PriceFareQuoteResponse`; DynaPath behavior remains the existing conditional allowlisted behavior and no local session is forced.
- R39 may expose internal typed request construction and `parse_product_train_inquiry_response`, but there is no client method and no read-only route until a normal `service_1` / `act_6` implementation is separately reviewed.

**Exact public request sequences:**

```text
R17 SENT/RECEIVED:
Device, Version, Key, qryDvCd, qryVal, abrdDtFrom, abrdDtTo, usePsbFlg

R17 PAYMENT_ELIGIBILITY:
Device, Version, Key, qryDvCd, qryVal

R31 a:
Device, Version, Key, jobDvCd, cmtrKndCd, psgCnt

R31 b:
Device, Version, Key, jobDvCd, cmtrKndCd, psgCnt,
cmtrUtlAgeCd repeated N times, psgPrnb repeated N times

R31 c:
Device, Version, Key, jobDvCd, psgCnt,
ogtkSaleWctNo, ogtkSaleDd, ogtkSaleSqno, ogtkRetPwd, inquiryType

R52:
Device, Version, Key, txtMenuId, chtnDvCd,
dptRsStnCd, arvRsStnCd, runDt, trnNo, gdNo, rqSeatAttCd,
trnGpCd, stlbTrnClsfCd
```

- [ ] **Step 1: Write failing variant, sequence, parser, DynaPath, and holdback tests**

  Test every exact sequence above including omission-vs-empty behavior. Prove R31 duplicates survive URL encoding in grouped order and arbitrary duplicate/extra fields are rejected. Prove R52 one/two-leg comma joins preserve leg order and `trnCnt` is absent. Test R17 HTTP 404 becomes one `KorailTransportError` with no retry. Add strict model/parser/error/repr coverage for R17/R31/R52 and the offline R39 response. Assert R39 has no client method/route even though DynaPath already recognizes its path.

- [ ] **Step 2: Run the focused file and verify RED**

  Run:

  ```bash
  PYTHONPATH="$PWD/src" pytest -q tests/test_next_variant_reads.py tests/test_http.py tests/test_public_contract.py tests/test_readme.py
  ```

  Expected: collection/import or assertion failures caused by missing tagged requests, ordered duplicate transport, parsers, methods, and route entries.

- [ ] **Step 3: Implement narrow ordered form support and the three public reads**

  Allow `httpx` form data to use a sequence of scalar `(name, value)` pairs only when the path's safety contract declares exact ordered variants. Keep existing mapping callers compatible. Validate the full field-name sequence after common insertion. Never accept a caller-controlled mapping. Add R17/R31/R52 to the exact read-only route boundary; do not add R39.

- [ ] **Step 4: Implement strict typed parsers and offline R39 contract**

  R17 rows preserve twelve nullable strings. R31 preserves its optional strings, primitive JSON integers, passenger rows, and raw data. R52 preserves six nullable strings per row and response order. R39 preserves the full statically declared train/recommended-product structure with repr-hidden strings/raw; nullable containers normalize predictably. No R39 transport call is possible.

- [ ] **Step 5: Run focused GREEN, full regression, compile, and diff checks**

  Run:

  ```bash
  PYTHONPATH="$PWD/src" pytest -q tests/test_next_variant_reads.py tests/test_http.py tests/test_public_contract.py tests/test_readme.py
  PYTHONPATH="$PWD/src" pytest -q -m "not live"
  python3 -m compileall -q src tests
  git diff --check
  ```

  Expected: all commands succeed; final boundary is `45` routes / `48` methods; `DYNAPATH_ALLOWLIST_PATHS` is unchanged; R39/R54 remain unreachable through the client.

- [ ] **Step 6: Document final scope and commit**

  Document seven static-contract public reads, R17's known 404/no-fallback status, R39/R54 holdbacks, exact DynaPath policy, unchanged live inventory, and zero mutation expansion. Commit with:

  ```bash
  git commit -m "feat: add closed variant read contracts"
  ```

---

## Final branch verification

After both task reviews are clean:

```bash
PYTHONPATH="$PWD/src" pytest -q -m "not live"
python3 -m compileall -q src tests
git diff --check
git status --short
```

Then run an independent whole-branch review. Only after that review is clean may a separately pinned, bounded, authenticated, read-only harness consider R13/R32/R43/R45/R52. Do not retry R17's known 404; do not call R31 without caller-derived discriminator data; do not call R39 or R54.
