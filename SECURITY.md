# Security

Report security concerns privately through the owner's existing private
channel. Include only the minimum sanitized detail needed to reproduce the
issue.

Do not disclose credentials, cookies, tokens, PNRs, raw responses, or
production identifiers in public issues, discussions, logs, fixtures, or
commits. Remove or replace those values before sharing any diagnostic output.

This package is read-only by default, but it is no longer read-only only.
Thirteen state-changing methods are implemented behind an explicit consent
gate, across seven independently opted-into categories: `reserve`,
`reserve_transfer`, `reserve_merge`, `reserve_with_discount_card` and
`confirm_standby_hold` (`reserve`); `cancel_unpaid_hold` (`cancel`);
`pay_with_fake_card` and `pay_with_card` (`payment`); `refund` (`refund`);
`add_to_cart` (`cart`); `register_discount_card` and `extend_discount_card`
(`discount_card`); and `recalculate_price` (`price_recalculation`). Each is
denied without a `MutationConsent` that opts into its category, each returns a
redacted preview and sends nothing under the default `dry_run=True`, and each
transmits only through a gated send path — `post_mutation_form` for the eight
POST routes and `get_mutation_query` for the one the app declares `@GET`.
Check-in, membership, point/mileage, and every other mutation endpoint remain
excluded and are not callable.

Both send paths apply the same four checks before anything leaves the process:
the consent must opt into the category, the exact `(method, path)` pair must be
a registered mutation route, the caller's category must be the one that OWNS
that route — so a consent for one category cannot be redirected to another's —
and the outgoing form must be flat string-to-string (or string-to-list, for the
one route that sends repeated keys) carrying the three common fields every
builder here writes. That last check refuses what a builder cannot produce and
a hand-assembled dict can: an integer that would encode unpadded, a boolean
that would encode as `"True"`, a `None`, a nested mapping.

This paragraph is enforced, not asserted: `tests/test_readme.py` derives the
method names from the client class rather than transcribing them, because the
list above was wrong for exactly as long as it was hand-maintained — it named
twelve methods and six categories after a seventh category shipped.

The payment form carries the card number in the clear, so a payment is gated
once more on which kind of card the consent claims. `pay_with_fake_card` refuses
unless `fake_card_only` is set and so can still only ever send a non-chargeable
test card. A real, chargeable card is reachable only through the separate
`pay_with_card`, and only on a consent that explicitly sets
`real_card_acknowledged=True` together with `fake_card_only=False`. Both flags
default to the safe side, so a consent that does not name the acknowledgement
cannot move money; the transmit gate independently refuses a payment whose
consent claims neither or both.

A security report must not exercise a real state change, must not use a
chargeable card, and must not make an unapproved production request. Real card
payment exists as a capability for the package owner's own account and own card;
it is not an invitation to charge anything while investigating a report.
