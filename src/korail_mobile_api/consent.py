"""Safe-by-default consent and preview types for KORAIL mutations.

This module is pure infrastructure: it carries the opt-in and dry-run preview
types that every future mutation method will use, but it adds no capability to
send a state-changing request. Nothing here performs I/O.

The safety posture is:

* A freshly constructed :class:`MutationConsent` grants nothing — every
  per-category ``allow_*`` flag defaults to ``False``.
* ``dry_run`` defaults to ``True``: a mutation call builds and validates its
  request, then returns a :class:`MutationPreview` **without sending**.
* ``fake_card_only`` defaults to ``True`` so a payment preview can only ever
  carry a non-chargeable test card.
* :func:`require_mutation_consent` denies by default, raising
  :class:`~korail_mobile_api.errors.MutationNotAllowedError` before any request
  is built unless the caller has explicitly opted into the exact category.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .errors import MutationNotAllowedError
from .redaction import redact_payload


MUTATION_CATEGORIES = ("reserve", "payment", "cancel", "refund")

_CONSENT_FLAG_BY_CATEGORY = {
    "reserve": "allow_reserve",
    "payment": "allow_payment",
    "cancel": "allow_cancel",
    "refund": "allow_refund",
}


@dataclass(frozen=True)
class MutationConsent:
    """Explicit, per-category opt-in for state-changing KORAIL requests.

    Each ``allow_*`` flag is an independent opt-in for exactly one category and
    defaults to ``False``; a consent grants only what is named explicitly.
    ``dry_run`` (default ``True``) makes a mutation call build-but-never-send,
    returning a :class:`MutationPreview`. ``fake_card_only`` (default ``True``)
    keeps any payment path restricted to a non-chargeable test card.
    """

    allow_reserve: bool = False
    allow_payment: bool = False
    allow_cancel: bool = False
    allow_refund: bool = False
    dry_run: bool = True
    fake_card_only: bool = True


@dataclass(frozen=True)
class MutationPreview:
    """The result of a dry-run mutation call: a described-but-unsent request.

    ``payload`` is always stored redacted — it is passed through
    :func:`~korail_mobile_api.redaction.redact_payload` on construction, so a
    ``MutationPreview`` can never hold raw card data or PII regardless of what
    the caller supplies. ``note`` documents that nothing was transmitted.
    """

    category: str
    method: str
    route: str
    payload: Mapping[str, str]
    note: str = "dry-run: not sent"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", redact_payload(self.payload))


def require_mutation_consent(
    consent: MutationConsent | None,
    category: str,
) -> None:
    """Deny a mutation unless ``consent`` explicitly opts into ``category``.

    ``category`` must be one of ``"reserve"``, ``"payment"``, ``"cancel"``,
    ``"refund"``. Raises :class:`~korail_mobile_api.errors.MutationNotAllowedError`
    when ``consent`` is ``None``, is not a :class:`MutationConsent`, names an
    unknown category, or when the matching ``allow_<category>`` flag is False.
    Returns ``None`` when the mutation is permitted. Performs no I/O.
    """
    flag = _CONSENT_FLAG_BY_CATEGORY.get(category)
    if flag is None:
        raise MutationNotAllowedError(
            f"unknown mutation category: {category!r}"
        )
    if not isinstance(consent, MutationConsent):
        raise MutationNotAllowedError(
            f"mutation category {category!r} requires an explicit "
            "MutationConsent"
        )
    if not getattr(consent, flag):
        raise MutationNotAllowedError(
            f"mutation category {category!r} is not permitted by the "
            "provided consent"
        )
