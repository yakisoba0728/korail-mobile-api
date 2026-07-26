"""Safe-by-default consent and preview types for KORAIL mutations.

This module is pure infrastructure: it carries the opt-in and dry-run preview
types that every future mutation method will use, but it adds no capability to
send a state-changing request. Nothing here performs I/O.

The safety posture is:

* A freshly constructed :class:`MutationConsent` grants nothing — every
  per-category ``allow_*`` flag defaults to ``False``.
* ``dry_run`` defaults to ``True``: a mutation call builds and validates its
  request, then returns a :class:`MutationPreview` **without sending**.
* ``fake_card_only`` defaults to ``True`` and ``real_card_acknowledged``
  defaults to ``False``, so a default consent can only ever carry a
  non-chargeable test card. A real, chargeable card requires the caller to
  invert BOTH flags explicitly (``fake_card_only=False,
  real_card_acknowledged=True``); setting neither, or setting both, is refused
  at the transmit gate.
* :func:`require_mutation_consent` denies by default, raising
  :class:`~korail_mobile_api.errors.MutationNotAllowedError` before any request
  is built unless the caller has explicitly opted into the exact category.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .errors import MutationNotAllowedError
from .redaction import redact_payload


MUTATION_CATEGORIES = (
    "reserve",
    "payment",
    "cancel",
    "refund",
    "discount_card",
    "price_recalculation",
)

_CONSENT_FLAG_BY_CATEGORY = {
    "reserve": "allow_reserve",
    "payment": "allow_payment",
    "cancel": "allow_cancel",
    "refund": "allow_refund",
    "discount_card": "allow_discount_card",
    "price_recalculation": "allow_price_recalculation",
}


@dataclass(frozen=True)
class MutationConsent:
    """Explicit, per-category opt-in for state-changing KORAIL requests.

    Each ``allow_*`` flag is an independent opt-in for exactly one category and
    defaults to ``False``; a consent grants only what is named explicitly.
    ``dry_run`` (default ``True``) makes a mutation call build-but-never-send,
    returning a :class:`MutationPreview`. ``fake_card_only`` (default ``True``)
    keeps any payment path restricted to a non-chargeable test card.

    ``real_card_acknowledged`` (default ``False``) is the single, explicit
    acknowledgement that a REAL, CHARGEABLE card number will be transmitted in
    the clear and that money will actually move. It is additive: because it
    defaults to ``False``, every consent written before it existed means exactly
    what it meant before, and the default posture is still fake-card-only.
    A real charge therefore needs both halves stated deliberately —
    ``fake_card_only=False`` (this is not a test card) and
    ``real_card_acknowledged=True`` (yes, charge it). The two are mutually
    exclusive claims: a consent that sets both is a caller bug and is refused
    rather than resolved in either direction, because an ambiguous consent is
    exactly the state a payment must never be sent on.
    """

    allow_reserve: bool = False
    allow_payment: bool = False
    allow_cancel: bool = False
    allow_refund: bool = False
    #: 할인카드(N카드) registration and 기간연장. A SEPARATE category rather
    #: than a reuse of ``allow_reserve``, because these two routes buy and
    #: extend a product: ``research.dcntCrdInfo.do`` answers with a
    #: ``lumpStlTgtNo`` that a payment then settles, and
    #: ``reservation.dcntCrdExtn.do`` extends a card's validity against its
    #: ticket credential. Nobody who opted into placing a train reservation
    #: also opted into buying a discount card, and no live-test path in this
    #: repository exercises this category.
    allow_discount_card: bool = False
    #: 보류된 PNR의 운임 재계산 (``certification.PriceReCalculation``). A
    #: category of its own, and deliberately NOT a reuse of any existing one.
    #:
    #: It is not ``allow_reserve``: the hold already exists and this creates
    #: nothing. It is not ``allow_cancel``/``allow_refund``: it destroys
    #: nothing. It is emphatically not ``allow_payment`` — that is the reuse
    #: that would actually be dangerous. A payment consent authorises settling
    #: a specific, already-quoted amount; this route REWRITES that amount
    #: server-side before it is settled, so folding it into ``allow_payment``
    #: would let a consent granted to pay ₩X silently authorise changing what
    #: ₩X is. And it is not ``allow_discount_card``: that category buys and
    #: extends a 할인카드 product, whereas this one applies discounts to a
    #: train reservation and never touches a card.
    #:
    #: Nobody who granted any of the five existing categories was asked about
    #: re-pricing a held booking, so it is asked for separately. No live-test
    #: path in this repository exercises it.
    allow_price_recalculation: bool = False
    dry_run: bool = True
    fake_card_only: bool = True
    #: The caller acknowledges that a real, chargeable PAN will be transmitted
    #: in the clear and that money will actually move. Never inferred, never
    #: defaulted on; see the class docstring.
    real_card_acknowledged: bool = False


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
    ``"refund"``, ``"discount_card"``, ``"price_recalculation"``. Raises :class:`~korail_mobile_api.errors.MutationNotAllowedError`
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
