"""상태변경 요청의 동의(consent)와 dry-run 미리보기 타입.

이 모듈 자체는 아무것도 전송하지 않는다. 상태변경 메서드가 요구하는 게이트
타입과, 전송 대신 돌아오는 미리보기 타입만 있다. I/O 없음.

기본값이 전부 막는 쪽이다.

* 갓 만든 :class:`MutationConsent` 는 아무 범주도 허용하지 않는다 —
  ``allow_*`` 가 전부 ``False``.
* ``dry_run`` 이 ``True`` 라, 상태변경 호출은 폼을 만들고 검증한 뒤
  :class:`MutationPreview` 를 돌려주며 **보내지 않는다**.
* 카드 종류 주장은 :class:`MutationConsent` 의 ``fake_card_only`` /
  ``real_card_acknowledged`` 두 플래그가 정한다. 규칙은 그 클래스에 적었다.
* :func:`require_mutation_consent` 는 폼을 만들기도 전에 막고
  :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError` 를 올린다.
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
    거절한다 — 모호한 consent 가 바로 결제를 보내면 안 되는 상태다. 둘 다
    끈 consent 도 같은 이유로 거절한다. 어느 종류의 카드인지 아무 주장도
    하지 않은 것이기 때문이다.

    카드 종류 주장이 결제를 열어 주지는 않는다. 카드번호를 들여다보는 코드는 없고,
    실제 청구를 가르는 것은 ``allow_payment`` 와 ``dry_run`` 이다.
    """

    allow_reserve: bool = False
    allow_payment: bool = False
    allow_cancel: bool = False
    allow_refund: bool = False
    #: 할인카드(N카드) 등록과 기간연장. ``allow_reserve`` 를 재사용하지 않고
    #: 따로 둔 것은 이 두 경로가 상품을 사고 늘리기 때문이다 —
    #: ``research.dcntCrdInfo.do`` 는 결제가 정산할 ``lumpStlTgtNo`` 를
    #: 돌려주고, ``reservation.dcntCrdExtn.do`` 는 카드의 유효기간을 늘린다.
    #: 열차 예약을 허락한 사람이 할인카드 구매까지 허락한 것은 아니다.
    #: 이 범주는 실제 서버에 대고 시험된 적이 없다.
    allow_discount_card: bool = False
    #: 보류된 PNR 의 운임 재계산(``certification.PriceReCalculation``).
    #:
    #: 특히 ``allow_payment`` 와 합치지 않았다. 결제 동의는 **이미 제시된
    #: 특정 금액** 을 정산하라는 뜻인데, 이 경로는 정산 전에 그 금액을 서버
    #: 쪽에서 다시 쓴다. 합쳤다면 "₩X 를 내라"는 동의가 "₩X 가 얼마인지를
    #: 바꿔도 좋다"까지 뜻하게 된다. 예약을 만들지도 지우지도 않으므로
    #: ``allow_reserve``/``allow_cancel``/``allow_refund`` 도 아니고, 카드를
    #: 건드리지 않으므로 ``allow_discount_card`` 도 아니다.
    #: 이 범주는 실제 서버에 대고 시험된 적이 없다.
    allow_price_recalculation: bool = False
    #: 장바구니에 승차권 담기(``cart.addCartList``,
    #: ``CartService.java:11-13``). 이미 존재하는 PNR 에 작용할 뿐 무엇을
    #: 만들지도 지우지도 않고 카드번호도 싣지 않아 ``allow_reserve`` 와
    #: 별개다. 이 범주는 실제 서버에 대고 시험된 적이 없다.
    allow_cart: bool = False
    dry_run: bool = True
    fake_card_only: bool = True
    #: 실제로 청구되는 카드번호가 평문으로 나가고 돈이 실제로 움직인다는 것을
    #: 호출자가 인정한다는 표시. 추론되지도 기본으로 켜지지도 않는다. 규칙은
    #: 클래스 docstring 에 있다.
    real_card_acknowledged: bool = False


@dataclass(frozen=True)
class MutationPreview:
    """dry-run 이 돌려주는 것 — 만들어졌지만 전송되지 않은 요청.

    ``payload`` 는 생성 시점에
    :func:`~korail_mobile_api.redaction.redact_payload` 를 통과해 저장되므로,
    호출자가 무엇을 넣었든 카드번호·비밀번호·이름·전화번호·회원번호가 그대로
    남지 않는다. ``note`` 는 전송되지 않았다는 표시다.

    **마스킹되는 것은 사람이 읽는 값이지 그 값을 대신하는 코드가 아니다.**
    운임 재계산 미리보기에서 ``hidDcntKndCd``/``dcnt_knd_cd1`` 은 평문으로
    남고, 그 코드표에는 국가유공자(``a6/C1042B.java:140``), 장애인
    보호자(``a6/s.java:441``), 국회의원(``:442``)이 들어 있다 — 숫자로 적힌
    민감정보다. 패키지 전체가 같은 비대칭을 갖는다
    (``is_sensitive_key("psgTpDvNm")`` 는 참, ``("psg_tp_dv_cd")`` 는 거짓).

    같은 미리보기 안의 연결 식별자(``hidPnrNo``, ``hidCustNo``,
    ``hidDscpNo``, ``hidFmlyNo``)는 모두 마스킹되므로 코드를 사람에게 붙일
    수는 없다. 그래도 제3자가 읽는 곳에 남기기 전에는 미리보기 전체를
    민감정보로 다뤄라.
    """

    category: str
    method: str
    route: str
    #: 값이 리스트인 것은 이상 상황이 아니다. ``redact_payload`` 는 같은 키가
    #: 반복되는 폼을 리스트로 보존하고, 앱도 운임 재계산에 여섯 개의
    #: ``@Field List<String>`` 를 선언한다(``CertificationService.java:35-37``).
    payload: Mapping[str, str | list[str]]
    note: str = "dry-run: not sent"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", redact_payload(self.payload))


def require_mutation_consent(
    consent: MutationConsent | None,
    category: MutationCategory,
) -> None:
    """``consent`` 가 ``category`` 를 명시적으로 허용하지 않으면 막는다.

    ``category`` 는 :data:`MutationCategory` 의 일곱 값 중 하나다. 타입이
    ``Literal`` 이라 타입 검사기가 일곱 개를 완성해 주고 그 밖의 값을
    거부한다. 런타임에 같은 목록이 필요하면
    :data:`MUTATION_CATEGORIES` 를 쓴다 — 순서와 길이를 약속하는 튜플이라
    최상위로 내보내지 않는다.

    ``consent`` 가 ``None`` 이거나 :class:`MutationConsent` 가 아니거나,
    모르는 범주이거나, 해당 ``allow_<범주>`` 가 거짓이면
    :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError` 를
    올린다. 허용되면 ``None`` 을 돌려준다. I/O 없음.
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
