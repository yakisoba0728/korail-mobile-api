# Security

Report security concerns privately through the owner's existing private
channel. Include only the minimum sanitized detail needed to reproduce the
issue.

Do not disclose credentials, cookies, tokens, PNRs, raw responses, or
production identifiers in public issues, discussions, logs, fixtures, or
commits. Remove or replace those values before sharing any diagnostic output.

This package is read-only by default, but it is no longer read-only only. Four
state-changing operations are implemented behind an explicit consent gate:
`reserve`, `cancel_unpaid_hold`, `pay_with_fake_card`, and `refund`. Each is
denied without a `MutationConsent` that opts into its category, each returns a
redacted preview and sends nothing under the default `dry_run=True`, and each
transmits only through the single gated send path. `pay_with_fake_card` refuses
unless `fake_card_only` is set, because the payment form carries the card
number in the clear. Check-in, membership, point/mileage, and every other
mutation endpoint remain excluded and are not callable.

A security report must not exercise a real state change, must not use a
chargeable card, and must not make an unapproved production request.
