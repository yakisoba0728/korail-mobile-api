"""``h_msg_cd`` → 예외 매핑과 이 패키지의 예외 계층.

.. code-block:: text

    KorailApiError                        모든 실패의 뿌리
    ├── KorailTransportError              HTTP 왕복 자체가 실패
    ├── KorailProtocolError               응답 모양이 프로토콜과 다름
    ├── KorailAuthError                   로그인·세션
    │   ├── KorailSessionExpiredError     P058
    │   └── KorailAuthContinuationRequired  WebView 후속 인증
    ├── KorailDynaPathError               안티매크로 거절(응답 헤더)
    ├── KorailAppError                    서버가 h_msg_cd 로 알린 실패
    │   ├── KorailNoResultsError
    │   │   └── KorailNoDirectTrainError
    │   ├── KorailSoldOutError
    │   ├── KorailSeatUnavailableError
    │   ├── KorailReservationRefusedError
    │   ├── KorailInvalidRequestError
    │   ├── KorailNotEntitledError
    │   ├── KorailServiceUnavailableError
    │   └── KorailAppUpdateRequiredError
    ├── KorailNetFunnelError              대기열(nf.letskorail.com)
    │   └── KorailQueueRejectedError
    └── KorailMutationNotAllowedError     consent 게이트

실패 판정은 ``strResult``(와 ``WRC000288``)이 합니다. 이 매핑은 이미 올라가기로
정해진 예외의 클래스만 고릅니다. 경고 코드를 달고 온 성공 응답은 그대로 성공입니다.

모든 메시지 문자열은 :func:`~korail_mobile_api.redaction.redact_text` 를 통과합니다.
"""

from .redaction import redact_text


class KorailApiError(Exception):
    """이 패키지의 모든 예외의 최상위.

    문자열 인자는 :func:`~korail_mobile_api.redaction.redact_text` 를 거칩니다.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            *(
                redact_text(arg) if isinstance(arg, str) else arg
                for arg in args
            )
        )


class KorailTransportError(KorailApiError):
    """HTTP 왕복이 실패해 앱 수준 응답을 파싱하지 못한 경우.

    읽기라면 재시도 가능. 상태변경이라면 요청이 서버에 닿았는지 알 수 없으므로
    예약목록·승차권목록으로 결과를 먼저 확인해야 합니다.
    """


class KorailProtocolError(KorailApiError):
    """응답이 JSON 이 아니거나 봉투 필드(``h_msg_cd``/``h_msg_txt``/``strResult``)가
    빠졌거나 타입이 다른 경우. 재시도해도 같은 응답이 옵니다.
    """


class KorailAuthError(KorailApiError):
    """로그인 실패 또는 세션 없이 인증 필요 메서드 호출."""


class KorailSessionExpiredError(KorailAuthError):
    """세션 만료. ``P058`` (``BaseActivity.java:610``).

    :class:`KorailAuthError` 의 하위이고 :class:`KorailAppError` 가 아닙니다.
    ``except KorailAppError`` 로는 잡히지 않습니다.
    """

    def __init__(
        self,
        code: str | None,
        message: str | None,
        *,
        raw: object | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'P058'}: "
            f"{redact_text(message or 'KORAIL session expired')}"
        )


class KorailDynaPathError(KorailApiError):
    """DynaPath 계층이 요청을 거절 — 안티매크로.

    ``h_msg_cd`` 가 아니라 응답 헤더(``DynaPath-Result`` 음수)로 옵니다.
    ``BaseDaoHelper.java:59-86``, ``BaseActivity.java:632-634``,
    ``ExecuteDao.java:25-47``.
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        raw: object | None = None,
    ) -> None:
        self.raw = raw
        super().__init__(
            redact_text(message or "KORAIL DynaPath request rejected")
        )


class KorailAuthContinuationRequired(KorailAuthError):
    """로그인이 WebView 2단계 인증으로 이어져야 합니다.

    :attr:`redirect_url` 과 :attr:`post_data` 를 넘겨 호출자가 브라우저로
    마쳐야 합니다.
    """

    def __init__(self, redirect_url: str, post_data: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.post_data = post_data
        self.raw = raw
        super().__init__("KORAIL login requires WebView continuation")


class KorailAppError(KorailApiError):
    """서버가 앱 수준 실패로 답함 — ``h_msg_cd`` 분류의 뿌리.

    ``strResult == "FAIL"`` 이거나 ``h_msg_cd == "WRC000288"`` 일 때 올라갑니다.
    매핑되지 않은 코드는 이 클래스 그대로 옵니다.

    실패 판정은 코드가 아니라 ``strResult`` 가 합니다. 앱도 인식하지 못한
    ``h_msg_cd`` 는 ``FAIL`` 이 아닌 응답에서 그냥 성공으로 흘려보냅니다
    (``BaseActivity.java:629``의 ``aVar = null``).
    """

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip()
        )


class KorailNoResultsError(KorailAppError):
    """요청은 이해됐고 맞는 것이 없었습니다.

    ``WRG000000``/``P114`` — APK 확인. 빈 화면 상태로 처리됨
    (``BaseActivity.java:326-337`` ``setErrorMsgCdNotShowDialog``,
    ``TicketListActivity.java:1393``).

    ``P100``/``WRT300005`` — APK 0건, 실서버 관측만.
    """


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 열차 없음, 환승으로는 가능. ``WRD000061``.

    앱은 ``DirectInquiryActivity.java:614-633`` 에서 환승 대화상자를 띄우고
    ``:284-296`` 에서 같은 질의를 ``TRANSFER_SQ_NO`` 로 다시 보냅니다.
    """


class KorailSoldOutError(KorailAppError):
    """재고 소진. ``ERR211161``.

    ``TCSOptionsActivity.java:551``, ``SpecialRoomUpgradeActivity.java:314``.
    ``strings.xml:2043`` = "잔여석이 부족하여 서비스를 제공할 수 없습니다."
    """


class KorailSeatUnavailableError(KorailAppError):
    """지정한 좌석은 줄 수 없으나 열차는 아직 예약 가능할 수 있습니다.

    * ``WRI411345`` — 자동 좌석 배정 제안(``SpecialRoomUpgradeActivity.java:312-313``)
    * ``ERR911081`` — 좌석선택 시간 경과, 자동 배정 제안(``a5/k.java:215-221``)
    * ``WRT800176`` — 좌석변경 불가 시간(``TCSOptionsActivity.java:557``)
    """


class KorailReservationRefusedError(KorailAppError):
    """예약 거절. 앱은 사용자를 기존 예약목록으로 보냅니다.

    ``WRR800029``, ``ERR911531``, ``ERR911051``.
    ``c5/a.java:174-177``, ``a5/k.java:208-214``.
    """


class KorailInvalidRequestError(KorailAppError):
    """필드 수준 검증 거부. 입력을 고쳐야 합니다.

    ``WRG200018``, ``WRT100002``, ``WRT100124``. APK 0건 — 실서버 관측만.
    """


class KorailNotEntitledError(KorailAppError):
    """이 계정에 그 할인·상품 자격이 없습니다. ``ERR299943``.

    APK 0건 — 실서버 관측만.
    """


class KorailServiceUnavailableError(KorailAppError):
    """KORAIL 백엔드 불가 선언. ``SEMGTK``.

    ``BaseActivity.java:608-609``. 앱은 저장된 승차권 화면을 제안합니다.
    """


class KorailAppUpdateRequiredError(KorailAppError):
    """서버가 앱 업데이트를 요구합니다. ``SUPDATE``.

    ``BaseActivity.java:613-619``. Google Play 로 보냄.
    """


class KorailNetFunnelError(KorailApiError):
    """NetFunnel 대기열이 거절·오작동·시간 초과.

    :class:`KorailAppError` 가 아닙니다 — ``h_msg_cd`` 를 갖지 않는 별도
    호스트의 별도 프로토콜입니다.
    """

    def __init__(
        self,
        code: str | None,
        message: str | None,
        *,
        raw: object | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip()
        )


class KorailQueueRejectedError(KorailNetFunnelError):
    """대기열이 아예 돌려보냄. ``TsBlock``(301) / ``TsIpBlock``(302).

    ``T6/g.java:892-894`` ``isBlocking()``.
    ``TsExpressNumber``(303)는 앱이 성공으로 셉니다(``T6/g.java:909`` ``isSuccess()``).
    """


class KorailMutationNotAllowedError(KorailApiError):
    """consent 없이 상태변경 요청을 시도했습니다.

    서버가 아니라 이 라이브러리가 막은 것입니다. 폼을 만들기도 전에 걸리므로
    아무것도 전송되지 않습니다.
    """


class KorailDynaPathRequiredError(KorailApiError):
    """DynaPath 가 필요한 경로인데 설정이 꺼져 있습니다.

    :data:`~korail_mobile_api.constants.DYNAPATH_ALLOWLIST_PATHS` 의 여섯 경로는
    토큰 없이 부르면 서버가 거절합니다. 이 라이브러리는 전송 전에 막습니다.
    :class:`KorailDynaPathError` 와 다릅니다 — 그쪽은 토큰을 보냈는데 서버가
    거절한 것이고, 이쪽은 아직 아무것도 보내지 않았습니다.
    """


# ---------------------------------------------------------------------------
# h_msg_cd -> exception mapping
#
# 코드로 가른다. 앱이 그렇게 하기 때문이다(BaseActivity.java:600-649). h_msg_txt 는
# 화면에 찍기만 한다(:625).
#
# 이 매핑이 해서는 안 되는 일: 이미 올라가기로 정해진 예외를 더 좁히는 것만
# 할 수 있다. 성공에 얹혀 오는, 결코 예외가 되어서는 안 되는 코드:
#   IRR000014, IRT800005, WRS800036, IRZ000001/S200, IRT000000/MRT200105,
#   WRR664296  (strResult=SUCC 와 취소 가능한 PNR 을 달고 온다)
# tests/test_error_classification.py 가 그것을 고정한다.
#
# 일부러 넣지 않은 것:
#   IRT010110  APK 전체 0건.
#   "MACRO"    이 앱의 안티매크로는 DynaPath-Result 헤더(KorailDynaPathError).
#   S198       MaaS 전용(BaseActivity.java:621). 이 라이브러리가 구현하지 않는 표면.
#   ERT800077  앱이 재시도를 권하나 이 라이브러리에 재시도 로직이 없다.
# ---------------------------------------------------------------------------

#: 빈 결과. ``WRG000000``/``P114`` APK 확인, ``P100``/``WRT300005`` 실서버 관측만.
NO_RESULT_CODES = frozenset({"WRG000000", "P114", "P100", "WRT300005"})

#: 직통 없음 → 환승 검색. APK 확인(``DirectInquiryActivity.java:620``).
NO_DIRECT_TRAIN_CODE = "WRD000061"

#: 재고 소진. APK 확인. srtgo 의 ``IRT010110`` 은 0건이라 제외.
SOLD_OUT_CODES = frozenset({"ERR211161"})

#: 좌석 불가. 열차는 아직 예약 가능할 수 있음.
SEAT_UNAVAILABLE_CODES = frozenset({"WRI411345", "ERR911081", "WRT800176"})

#: 예약 거절. 앱은 예약목록으로 보냄.
RESERVATION_REFUSED_CODES = frozenset({"WRR800029", "ERR911531", "ERR911051"})

#: 필드 검증 거부. APK 0건 — 실서버 관측만.
INVALID_REQUEST_CODES = frozenset({"WRG200018", "WRT100002", "WRT100124"})

#: 자격 없음. APK 0건 — 실서버 관측만.
NOT_ENTITLED_CODES = frozenset({"ERR299943"})

#: 백엔드 불가. APK 확인(``BaseActivity.java:608``).
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

#: 앱 업데이트 요구. APK 확인(``BaseActivity.java:613``).
APP_UPDATE_REQUIRED_CODE = "SUPDATE"

#: 세션 만료. 이 매핑보다 앞에서 :class:`KorailSessionExpiredError` 로 처리됨.
SESSION_EXPIRED_CODE = "P058"

_APP_ERROR_BY_CODE: dict[str, type[KorailAppError]] = {
    **{code: KorailNoResultsError for code in NO_RESULT_CODES},
    NO_DIRECT_TRAIN_CODE: KorailNoDirectTrainError,
    **{code: KorailSoldOutError for code in SOLD_OUT_CODES},
    **{code: KorailSeatUnavailableError for code in SEAT_UNAVAILABLE_CODES},
    **{
        code: KorailReservationRefusedError
        for code in RESERVATION_REFUSED_CODES
    },
    **{code: KorailInvalidRequestError for code in INVALID_REQUEST_CODES},
    **{code: KorailNotEntitledError for code in NOT_ENTITLED_CODES},
    SERVICE_UNAVAILABLE_CODE: KorailServiceUnavailableError,
    APP_UPDATE_REQUIRED_CODE: KorailAppUpdateRequiredError,
}


def classify_app_error(
    code: str | None,
    message: str | None,
    *,
    raw: object | None = None,
) -> KorailAppError:
    """``h_msg_cd`` 가 뒷받침하는 가장 구체적인 :class:`KorailAppError` 를 만듭니다.

    올리지 않고 **돌려줍니다** — 각 호출 지점이 자기 ``raise`` 와 트레이스백을
    유지하게 하기 위해서입니다. 모르는 코드는 밋밋한 :class:`KorailAppError`.

    이미 올리기로 한 자리에서만 부르십시오. 성공 응답의 코드를 넘기면 서버가
    알리지도 않은 실패를 만들게 됩니다.

    ``P058`` 은 여기서 다루지 않습니다 — 이 매핑을 보기 전에
    :class:`KorailSessionExpiredError` 로 처리됩니다.
    """
    subclass = _APP_ERROR_BY_CODE.get(code or "", KorailAppError)
    return subclass(code, message, raw=raw)
