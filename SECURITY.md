# Security

Report security concerns privately through the owner's existing private
channel. Include only the minimum sanitized detail needed to reproduce the
issue.

Do not disclose credentials, cookies, tokens, PNRs, raw responses, or
production identifiers in public issues, discussions, logs, fixtures, or
commits. Remove or replace those values before sharing any diagnostic output.

This package is read-only by default, but it is no longer read-only only. Twelve
state-changing methods are implemented behind an explicit consent gate, across
six independently opted-into categories: `reserve`, `reserve_transfer`,
`reserve_merge`, `reserve_with_discount_card` and `confirm_standby_hold`
(`reserve`); `cancel_unpaid_hold` (`cancel`); `pay_with_fake_card` and
`pay_with_card` (`payment`); `refund` (`refund`); `register_discount_card` and
`extend_discount_card` (`discount_card`); and `recalculate_price`
(`price_recalculation`). Each is
denied without a `MutationConsent` that opts into its category, each returns a
redacted preview and sends nothing under the default `dry_run=True`, and each
transmits only through the single gated send path. Check-in, membership,
point/mileage, and every other mutation endpoint remain excluded and are not
callable.

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
