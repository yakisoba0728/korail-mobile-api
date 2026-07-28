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
  :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError` before any request
  is built unless the caller has explicitly opted into the exact category.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .errors import KorailMutationNotAllowedError
from .redaction import redact_payload


MUTATION_CATEGORIES = (
    "reserve",
    "payment",
    "cancel",
    "refund",
    "discount_card",
    "price_recalculation",
    "cart",
)

#: :func:`require_mutation_consent` 가 아는 일곱 가지 상태변경 범주. 서버가 주는
#: 코드가 아니라 이 라이브러리 자신의 게이트 어휘이므로 집합이 완전히 닫혀 있다 —
#: 각 값은 :class:`MutationConsent` 의 ``allow_<범주>`` 플래그 하나에 대응한다.
#: ``"reserve"`` 예약, ``"payment"`` 결제, ``"cancel"`` 예약취소, ``"refund"``
#: 환불, ``"discount_card"`` 할인카드 등록·해지, ``"price_recalculation"`` 운임
#: 재계산, ``"cart"`` 장바구니. :data:`MUTATION_CATEGORIES` 는 같은 값들의 런타임
#: 형태다.
MutationCategory = Literal[
    "reserve",
    "payment",
    "cancel",
    "refund",
    "discount_card",
    "price_recalculation",
    "cart",
]

_CONSENT_FLAG_BY_CATEGORY = {
    "reserve": "allow_reserve",
    "payment": "allow_payment",
    "cancel": "allow_cancel",
    "refund": "allow_refund",
    "discount_card": "allow_discount_card",
    "price_recalculation": "allow_price_recalculation",
    "cart": "allow_cart",
}


@dataclass(frozen=True)
class MutationConsent:
    """상태를 바꾸는 KORAIL 요청에 범주별로 따로 주는 명시적 동의.

    ``allow_*`` 플래그는 범주 하나씩에 독립으로 붙고 전부 ``False`` 가 기본이다 —
    consent 는 이름을 적은 것만 허락한다. ``dry_run`` 은 ``True`` 가 기본이라,
    상태 변경 메서드는 폼을 만들어 검증만 하고 :class:`MutationPreview` 를
    돌려주며 아무것도 전송하지 않는다.

    ``fake_card_only``(기본 ``True``)와 ``real_card_acknowledged``(기본
    ``False``)는 어떤 종류의 카드를 보낸다고 주장하는지를 적는 자리이고, 서로
    배타적이다. **실제로 청구되는 카드를 쓰려면 두 쪽을 다 적어야 한다** —
    ``fake_card_only=False``(시험카드가 아니다)와
    ``real_card_acknowledged=True``(청구돼도 좋다)를 함께 켜야
    :meth:`~korail_mobile_api.client.KorailClient.pay_with_card` 가 통과한다.
    기본값 그대로는 :meth:`~korail_mobile_api.client.KorailClient.pay_with_fake_card`
    쪽만 열린다. 둘 다 켠 consent 는 모순이라 어느 쪽으로도 해석하지 않고
    거절한다 — 모호한 consent 가 바로 결제를 보내면 안 되는 상태다.

    카드 종류 주장이 결제를 열어 주지는 않는다. 카드번호를 들여다보는 코드는 없고,
    실제 청구를 가르는 것은 ``allow_payment`` 와 ``dry_run`` 이다.
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
    #: 장바구니에 승차권 담기 (``cart.addCartList``,
    #: ``CartService.java:11-13``). Its own category rather than a reuse of
    #: ``allow_reserve``: it acts on a PNR that already exists, creates and
    #: destroys nothing this package can observe, and carries no card number.
    #: No live-test path in this repository exercises it.
    allow_cart: bool = False
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
    ``MutationPreview`` can never hold a raw PAN, a password, a name, a phone
    number or a membership/customer number regardless of what the caller
    supplies. ``note`` documents that nothing was transmitted.

    What that does NOT cover, stated plainly because the sentence above used
    to say "or PII" and that was too broad: redaction masks the values a
    human can read, not the **codes** that stand for them. A preview of a
    운임 재계산 keeps ``hidDcntKndCd`` / ``dcnt_knd_cd1`` in the clear, and
    those code tables include 국가유공자 (``a6/C1042B.java:140``), 장애인
    보호자 (``a6/s.java:441``) and 국회의원 (``:442``) — special-category
    facts about a person, spelled as digits. The same asymmetry runs through
    the package on purpose (``is_sensitive_key("psgTpDvNm")`` is True,
    ``is_sensitive_key("psg_tp_dv_cd")`` is False), and the read parsers
    return the same codes unmasked. It is survivable here because every
    linking identifier in the same preview (``hidPnrNo``, ``hidCustNo``,
    ``hidDscpNo``, ``hidFmlyNo``) IS masked, so a code cannot be attached to
    a person, and because the value is the caller's own input coming back
    inside their own process. Treat a preview as sensitive anyway before
    logging it somewhere a third party reads.
    """

    category: str
    method: str
    route: str
    #: A list value is legitimate here, not an anomaly: ``redact_payload``
    #: preserves repeated wire keys as a list, and the app itself declares six
    #: ``@Field List<String>`` parameters on 운임 재계산
    #: (``CertificationService.java:35-37``).
    payload: Mapping[str, str | list[str]]
    note: str = "dry-run: not sent"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", redact_payload(self.payload))


def require_mutation_consent(
    consent: MutationConsent | None,
    category: MutationCategory,
) -> None:
    """Deny a mutation unless ``consent`` explicitly opts into ``category``.

    ``category`` must be one of ``"reserve"``, ``"payment"``, ``"cancel"``,
    ``"refund"``, ``"discount_card"``, ``"price_recalculation"``,
    ``"cart"`` — the parameter's type is
    :data:`~korail_mobile_api.consent.MutationCategory`, so a type checker
    completes the seven and rejects anything else. The runtime form of the same
    list is :data:`~korail_mobile_api.consent.MUTATION_CATEGORIES`, importable
    as ``from korail_mobile_api.consent import MUTATION_CATEGORIES``. That tuple
    stays off the top level: it is ordered, and an eighth category would change
    what its order and length promise. The ``Literal`` has neither property, so
    widening it later is additive.
    Raises :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError`
    when ``consent`` is ``None``, is not a :class:`MutationConsent`, names an
    unknown category, or when the matching ``allow_<category>`` flag is False.
    Returns ``None`` when the mutation is permitted. Performs no I/O.
    """
    flag = _CONSENT_FLAG_BY_CATEGORY.get(category)
    if flag is None:
        raise KorailMutationNotAllowedError(
            f"unknown mutation category: {category!r}"
        )
    if not isinstance(consent, MutationConsent):
        raise KorailMutationNotAllowedError(
            f"mutation category {category!r} requires an explicit "
            "MutationConsent"
        )
    if not getattr(consent, flag):
        raise KorailMutationNotAllowedError(
            f"mutation category {category!r} is not permitted by the "
            "provided consent"
        )
