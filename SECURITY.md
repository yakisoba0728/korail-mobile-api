# Security

Report security concerns privately through the owner's existing private
channel. Include only the minimum sanitized detail needed to reproduce the
issue.

Do not disclose credentials, cookies, tokens, PNRs, raw responses, or
production identifiers in public issues, discussions, logs, fixtures, or
commits. Remove or replace those values before sharing any diagnostic output.

This package intentionally excludes reservation, payment, cancellation,
refund, check-in, membership, and other mutation endpoints. A security report
must not exercise excluded mutations or make an unapproved production request.
