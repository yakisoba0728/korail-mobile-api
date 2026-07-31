"""상태변경 요청의 동의(consent)와 dry-run 미리보기 타입.

이 모듈 자체는 I/O 없음. 상태변경 메서드가 요구하는 게이트 타입과, 전송 대신
돌아오는 미리보기 타입만 있습니다.

기본값이 전부 막는 쪽:

* ``allow_*`` 전부 ``False``
* ``dry_run = True`` → :class:`MutationPreview` 를 돌려주며 전송하지 않음
* ``fake_card_only = True``, ``real_card_acknowledged = False``
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

#: 일곱 가지 상태변경 범주. 각 값은 :class:`MutationConsent` 의 ``allow_<범주>``
#: 플래그 하나에 대응합니다.
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
    """범주별 명시적 동의.

    ``fake_card_only``/``real_card_acknowledged`` 규칙: 실제 청구 카드를
    쓰려면 ``fake_card_only=False, real_card_acknowledged=True`` 를 함께 켜야
    합니다. 둘 다 켜거나 둘 다 끄면 거절됩니다.
    """

    allow_reserve: bool = False
    allow_payment: bool = False
    allow_cancel: bool = False
    allow_refund: bool = False
    #: 할인카드(N카드) 등록·기간연장. 서버 미시험.
    allow_discount_card: bool = False
    #: 운임 재계산(``certification.PriceReCalculation``). 서버 미시험.
    allow_price_recalculation: bool = False
    #: 장바구니(``cart.addCartList``, ``CartService.java:11-13``). 서버 미시험.
    allow_cart: bool = False
    dry_run: bool = True
    fake_card_only: bool = True
    real_card_acknowledged: bool = False


@dataclass(frozen=True)
class MutationPreview:
    """dry-run 결과 — 만들어졌지만 전송되지 않은 요청.

    ``payload`` 는 생성 시점에 :func:`~korail_mobile_api.redaction.redact_payload`
    를 통과합니다. 마스킹되는 것은 사람이 읽는 값이지 코드가 아닙니다
    (``is_sensitive_key("psgTpDvNm")`` 참, ``("psg_tp_dv_cd")`` 거짓).
    """

    category: str
    method: str
    route: str
    payload: Mapping[str, str | list[str]]
    note: str = "dry-run: not sent"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", redact_payload(self.payload))


def require_mutation_consent(
    consent: MutationConsent | None,
    category: MutationCategory,
) -> None:
    """``consent`` 가 ``category`` 를 명시적으로 허용하지 않으면 막습니다.

    ``None``/잘못된 타입/모르는 범주/해당 ``allow_<범주>`` 거짓이면
    :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError`. I/O 없음.
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
