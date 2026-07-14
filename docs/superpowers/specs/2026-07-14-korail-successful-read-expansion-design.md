# KORAIL Successful Read Expansion Design

**Date:** 2026-07-14

**Status:** Implemented and offline-verified on 2026-07-14

## Goal

Expose every KORAIL endpoint that already has a recorded successful production
read but is still outside the Python package, and expose the already-allowlisted
service-status cache through a public method. The result is eleven new public
read operations without adding reservation, payment, refund, cancellation,
check-in, member mutation, point/mileage mutation, or other side-effect routes.

## Context

The current package is clean on `main` at `a29a19a`. It allows fifteen exact
login/read routes and its recorded final offline result is `275 passed, 1
skipped`, with the skipped test being the explicit live-service opt-in.

The APK/runtime inventory records twenty-five successful endpoint entries. Ten
of those successful reads do not yet have a route or public wrapper in the
package:

- cart list;
- deposit-bank list;
- delay-discount ticket list;
- discount-coupon list;
- pass available dates;
- trip/pass menu;
- product reservation list;
- product reservation detail;
- ticket receipt;
- reservation history.

`GET /file/CACHE/MobileService.cache` is already one of the fifteen allowed
routes but has no public `KorailClient` method. It is included in this phase, so
the public surface gains eleven methods while the route boundary grows by only
ten routes, from fifteen to twenty-five.

No new live request is required. Request shapes and response fields come from
the committed APK contract catalog, and prior live evidence establishes that
the endpoints are reachable. New fixtures must be synthetic and sanitized.

## Chosen Architecture

Keep the existing client, transport, and safety layers, but isolate the larger
new surface in three focused modules:

- `read_models.py`: immutable public response and item types;
- `read_payloads.py`: exact, validated request dictionaries;
- `read_parsers.py`: strict envelope/shape parsing and typed conversion.

`KorailClient` remains the single public entry point. The new types are
re-exported from the package root. Existing `models.py`, `payloads.py`, and
`parsers.py` are not reorganized; this phase adds no unrelated refactor.

This is preferred over placing every type and parser into the existing central
files, which would make them materially harder to review, and over raw-only
wrappers, which would leave the caller without a stable public contract.

## Scope

### In scope

- Eleven public `KorailClient` methods.
- Ten newly allowed exact read routes.
- Exact form/query key boundaries for all eleven operations.
- Conservative typed models for stable, useful fields.
- Caller-accessible but repr-hidden raw mappings and sensitive identifiers.
- Route-specific empty-result handling for already evidenced no-data codes.
- Synthetic fixtures, TDD coverage, documentation, package verification, and
  one final whole-feature review.

### Out of scope

- Any live-service replay in this phase.
- New live-helper calls or new environment variables.
- Reservation creation, change, cancellation, or waitlisting.
- Payment, refund, compensation, cash-receipt issuance, or check-in.
- Cart mutation, product cancellation, or pass purchase/reservation.
- MAAS reservation-linked status, detail, payment, or cancellation.
- Server logout, member mutation, push/SMS, point/mileage mutation, and gifts.
- New DynaPath routes, NetFunnel support, or WebView/native automation.
- Exhaustively modeling every field found only in static APK classes.

## Public API

`KorailClient` gains these methods:

```python
def get_service_status(
    self,
    timestamp_ms: int | None = None,
) -> ServiceStatusResponse: ...

def get_cart_list(
    self,
    pnr_no: str = "",
    additional_service_request_no: str = "",
) -> CartListResponse: ...

def get_deposit_banks(self) -> DepositBankListResponse: ...

def get_delay_discount_tickets(
    self,
    departure_date_to: str,
) -> DelayDiscountTicketListResponse: ...

def get_discount_coupons(
    self,
    page_no: int = 1,
    pnr_no: str = "",
) -> DiscountCouponListResponse: ...

def get_pass_available_dates(
    self,
    kind_code: str,
    period_code: str,
    age_code: str,
) -> PassAvailabilityResponse: ...

def get_trip_menu(self) -> TripMenuResponse: ...

def get_product_reservations(
    self,
    page_no: int = 1,
    page_size: int = 20,
) -> ProductReservationListResponse: ...

def get_product_detail(
    self,
    reservation_no: str,
    reservation_sequence: str,
) -> ProductDetailResponse: ...

def get_ticket_receipt(
    self,
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
) -> TicketReceiptResponse: ...

def get_reservation_history(self) -> ReservationHistoryResponse: ...
```

The package public-method count becomes twenty-eight. No aliases using the APK
Java method names are added.

## Authentication Policy

These reads are account-neutral or parameter-only and do not require a local
authenticated-session precondition:

- `get_service_status()`;
- `get_deposit_banks()`;
- `get_pass_available_dates()`;
- `get_trip_menu()`.

These reads expose account, reservation, coupon, product, or ticket data and
require `KorailSessionClient.current` before request construction:

- `get_cart_list()`;
- `get_delay_discount_tickets()`;
- `get_discount_coupons()`;
- `get_product_reservations()`;
- `get_product_detail()`;
- `get_ticket_receipt()`;
- `get_reservation_history()`.

A missing local session raises `KorailAuthError` before transport I/O. Existing
`P058` handling continues to clear local session state and raise
`KorailSessionExpiredError`.

## Request Contracts

Every request uses the canonical `https://smart.letskorail.com` origin. The
exact requests are:

| Public method | HTTP/path | Exact query or form keys |
|---|---|---|
| `get_service_status` | `GET /file/CACHE/MobileService.cache` | `timeStamp` |
| `get_cart_list` | `POST /classes/com.korail.mobile.cart.showCartList` | `Device`, `Version`, `Key`, `pnrNo`, `addSrvReqNo` |
| `get_deposit_banks` | `POST /classes/com.korail.mobile.dlay.dptnBank.do` | `Device`, `Version`, `Key` |
| `get_delay_discount_tickets` | `POST /classes/com.korail.mobile.passCard.DelayDiscountView` | `Device`, `Version`, `Key`, `dptDtTo` |
| `get_discount_coupons` | `POST /classes/com.korail.mobile.passCard.CouponView` | `Device`, `Version`, `Key`, `txtSelPage`, `pnrNo` |
| `get_pass_available_dates` | `POST /classes/com.korail.mobile.pass.passInfoList` | `Device`, `Version`, `Key`, `txtCmtrKndCd`, `txtCmtrUtlTrmCd`, `txtCmtrUtlAgeCd` |
| `get_trip_menu` | `POST /classes/com.korail.mobile.pass.trGdMenuLt.do` | `Device`, `Version` |
| `get_product_reservations` | `GET /classes/com.korail.mobile.product.ReservationList` | `Device`, `Version`, `Key`, `txtSelPage`, `txtCntPerPage` |
| `get_product_detail` | `GET /classes/com.korail.mobile.product.ReservationDetail` | `Device`, `Version`, `Key`, `txtVrRsNo`, `txtVrRsvSqNo` |
| `get_ticket_receipt` | `POST /classes/com.korail.mobile.receipt.ReceiptInfo` | `Device`, `Version`, `Key`, `h_orgtk_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_tk_ret_pwd` |
| `get_reservation_history` | `GET /classes/com.korail.mobile.reservation.ReservationView` | `Device`, `Version`, `Key` |

The product-detail query deliberately uses `txtVrRsNo`, the exact Retrofit
annotation recorded for the live-successful route. The similarly named
`txtVrRsvNo` field from a request model is not substituted.

The safety layer validates exact field sets after common-field composition for
both GET and POST requests. Mapping values must be scalar strings or integers;
list values that could produce duplicate keys are rejected. Unknown keys,
missing keys, duplicate query keys, embedded URL queries, alternate methods,
encoded path spellings, and off-origin targets fail before I/O.

No new route is added to `DYNAPATH_ALLOWLIST_PATHS`. All eleven methods call
their route with DynaPath disabled explicitly, so a caller-supplied custom
DynaPath allowlist cannot attach a token to these reads.

## Input Validation

- `timestamp_ms` uses the existing cache-query contract: `None` means current
  Unix milliseconds; otherwise `type(value) is int and value >= 0`.
- `departure_date_to` and `sale_date` require exactly eight ASCII digits.
- `page_no` and `page_size` require positive non-boolean integers.
- Pass `kind_code`, `period_code`, and `age_code` require non-empty strings.
- Product `reservation_no` and `reservation_sequence` require non-empty
  strings.
- Receipt `window_no`, `sale_sequence`, and `return_password` require
  non-empty strings. Their undocumented width is not invented.
- Cart `pnr_no` and `additional_service_request_no` remain optional empty
  strings because the recorded contract allows account/current-context
  lookups without inventing identifiers.
- Coupon `pnr_no` remains optional for the same reason.

All validation runs before transport I/O. Strings are sent exactly after
non-empty/shape validation; sensitive identifiers are never normalized,
logged, or persisted.

## Models

All new dataclasses are frozen. Every response inherits the existing base
envelope fields and retains `raw` with `repr=False`. Every nested item also
retains its original mapping through a repr-hidden `raw` field.

### Service, cart, and bank

- `ServiceStatusResponse`: typed base envelope for the service cache.
- `CartItem`: service code, provider name, product name, item type, departure
  date, received amount, reservation-received date, ticket count, and usage
  window. Partner reservation number, PNR, lump-sum target number, customer
  number, and virtual reservation number are repr-hidden.
- `CartListResponse`: immutable `items: tuple[CartItem, ...]`.
- `DepositBank`: code and display name.
- `DepositBankListResponse`: immutable `items: tuple[DepositBank, ...]`.

### Discounts and passes

- `DelayDiscountTicket`: fare and usable-until date. Original sale date,
  window number, sequence, and return password are repr-hidden.
- `DelayDiscountTicketListResponse`: immutable ticket tuple.
- `DiscountCoupon`: guide, expiration date, discount values, and remarks.
  Coupon number is repr-hidden.
- `DiscountCouponListResponse`: immutable coupon tuple plus current and total
  page numbers.
- `PassOffice`: English/code value and Korean/display value.
- `PassAvailabilityResponse`: immutable open-date strings, ticket-issue-date
  strings, and office tuple.
- `TripMenuContent`: title, detail, type, active/agree flags, and info. Image and
  URL values are repr-hidden.
- `TripMenuItem`: title, detail, type, button, immutable contents, and a
  repr-hidden URL.
- `TripMenuResponse`: immutable menu tuple and popup message.

### Products, receipts, and reservation history

- `ProductReservation`: product name, reservation status, payment deadline,
  and payment status. Virtual reservation number is repr-hidden.
- `ProductReservationListResponse`: immutable item tuple and total count.
- `ProductDetailResponse`: product name, reservation status, cancellation
  deadline/amount/fee, received amount, total amount, usage period, immutable
  included-item names, and a repr-hidden virtual reservation number.
- `ReceiptPayment`: payment method, approval date, installment months, and
  amount. Account, approval, card, and point numbers are repr-hidden.
- `TicketReceipt`: travel date, stations/times, train/class fields, passenger
  counts, received/refund/fee amounts, and immutable payments. Member-card
  number is repr-hidden.
- `TicketReceiptResponse`: immutable receipt tuple.
- `ReservationHistoryTrain`: stations/times, run date, train number/class,
  reservation/payment flags, and seat/standing counts. PNR is repr-hidden.
- `ReservationHistoryResponse`: immutable flattened train tuple while the
  original journey nesting remains available only through repr-hidden `raw`.

Known APK numeric fields normalize an integer or an ASCII decimal string to an
integer. `None` stays `None`; booleans, non-decimal strings, and other types are
protocol errors. Unknown fields are not promoted to public attributes and
remain available through `raw`.

## Parser And Empty-Result Policy

Each parser first validates a mapping response and the common envelope. Nested
wrapper objects such as `cart_infos.cart_info`, `disc_infos.disc_info`, and
`receipt_infos.receipt_info` normalize missing or null collections to empty
tuples. A present collection with the wrong type, or a present item that is not
a mapping, raises `KorailProtocolError`.

The only route-specific no-data codes accepted as successful empty results are
the already recorded cases:

- discount coupons: `WRG000000`;
- reservation history: `P100`.

The parsers return the relevant typed response with an empty item tuple while
preserving the envelope and raw mapping. `P058` always remains session expiry.
Any other `strResult=FAIL` or unexpected application failure raises
`KorailAppError`; HTTP, JSON, and protocol failures retain existing typed error
classes.

## Data Flow

1. The public method enforces its local authentication and argument contract.
2. A focused payload builder creates only the documented caller fields.
3. The HTTP layer composes common fields where required.
4. The safety layer verifies canonical origin, exact method/path, exact final
   field set, scalar field values, and explicit DynaPath disablement.
5. The request is issued once; there is no fallback route or retry.
6. Existing HTTP/JSON/session classification runs.
7. The focused parser returns frozen typed models and repr-hidden raw data.

No method chains into a mutation, follows a response URL, calls a product
detail automatically, or synthesizes a PNR/ticket/reservation identifier.

## Safety And Redaction

- Route count is exactly twenty-five after the ten additions.
- The existing DynaPath algorithm and allowlist remain byte-for-byte unchanged.
- Reservation, payment, refund, cancellation, check-in, member mutation,
  point/mileage mutation, and push/SMS paths remain absent from the HTTP route
  boundary.
- The new request builders do not expose arbitrary `dict` or extra-field
  arguments.
- Full responses, request identifiers, cookies, credentials, and session data
  are never included in live-helper output, documentation examples, or test
  failure messages.
- Synthetic fixture values are unmistakably fake and contain no captured
  production response text.

## Test Strategy

Every production behavior is developed test-first and observed failing before
implementation.

### Payload and transport tests

- Exact method/path and exact query/form fields for all eleven methods.
- Validation failure before I/O for dates, pagination, pass codes, product
  identifiers, and receipt identifiers.
- No DynaPath provider invocation even when a custom allowlist includes a new
  route.
- Rejection of missing/unknown fields, non-scalar values, wrong methods,
  encoded paths, embedded queries, and mutation paths before transport.
- Exactly one request per method and no adjacent call.

### Parser and model tests

- Synthetic success fixtures for every response family.
- Empty wrapper normalization and the two evidenced no-data codes.
- Wrong wrapper/list/item/numeric types raise `KorailProtocolError`.
- Unexpected application failure and `P058` keep existing typed behavior.
- All sensitive identifiers and every raw mapping stay out of `repr()` while
  remaining caller-accessible.

### Public and regression tests

- Exact new method signatures, return hints, and package-root exports.
- Local authentication requirements and pre-login account-neutral behavior.
- Session-expiry clearing through every new authenticated family.
- Existing login, cache, UUID/MAAS, DynaPath, search, schedule, transfer, and
  ticket behaviors remain unchanged.
- README examples and progress/status counts match the public contract.

No live test is added or run for this phase. The existing explicit live opt-in
remains the only default suite skip.

## Files And Responsibilities

- `src/korail_mobile_api/read_models.py`: new immutable public models.
- `src/korail_mobile_api/read_payloads.py`: exact input validation and request
  builders.
- `src/korail_mobile_api/read_parsers.py`: envelope, empty-result, wrapper, and
  item parsing.
- `src/korail_mobile_api/safety.py`: ten routes and exact GET/POST field
  contracts.
- `src/korail_mobile_api/http.py`: apply exact query validation and scalar-value
  safety after common-field composition.
- `src/korail_mobile_api/client.py`: eleven public methods and auth boundaries.
- `src/korail_mobile_api/__init__.py`: package-root model exports.
- `tests/fixtures/`: synthetic response fixtures only.
- `tests/test_successful_read_expansion.py`: endpoint payload, orchestration,
  parser, model, empty-result, and auth tests.
- `tests/test_http.py`: low-level exact query/form and DynaPath regressions.
- `tests/test_public_contract.py`: method/export/signature contract.
- `tests/test_redaction_safety.py`: sensitive request/response repr and error
  coverage.
- `README.md`: public usage and safety documentation.
- `docs/api-status-by-service.md`: document package coverage for the ten reads
  without changing their historical runtime status.
- `docs/library-build-guide.md`: correct the stale `24/8/133` count.
- `docs/IMPLEMENTATION_PROGRESS.md`: record the actual final implementation and
  verification evidence.
- `NEXT_SESSION_PROMPT.md`: refresh the shared head and handoff after final
  integration.

## Implementation And Review Strategy

Implementation is divided into independently testable endpoint families:

1. exact safety/query infrastructure and service status;
2. deposit banks, pass availability, and trip menu;
3. cart, delay discounts, and discount coupons;
4. product list and detail;
5. ticket receipt and reservation history;
6. public documentation, package verification, and integration cleanup.

Each family follows red-green-refactor and is committed separately. Per the
user's explicit preference, there is one whole-feature code review after all
families are implemented, followed by one consolidated fix pass for every
confirmed finding.

## Completion Criteria

- All eleven public methods and their documented return types are available.
- All ten previously successful but unimplemented routes are callable only
  through exact read contracts.
- `KORAIL_READ_ONLY_ROUTES` contains exactly twenty-five entries.
- Every new route explicitly bypasses DynaPath; the existing generator and
  DynaPath allowlist are unchanged.
- Known empty-result codes return typed empty collections; all other failures
  remain typed errors.
- Sensitive values and raw mappings remain accessible but repr-hidden.
- No live request, captured raw response, credential, cookie, PNR, ticket
  value, card value, or DynaPath token is persisted.
- The complete offline suite passes with only the existing explicit live skip.
- Wheel and source distribution build successfully, and a fresh environment
  installs the wheel and imports the eleven new response types and
  `KorailClient`.
- Static scans confirm mutation routes remain excluded.
- One final whole-feature review has no open Critical or Important finding.
- Documentation and the shared handoff reflect the actual final head and
  verification results.
