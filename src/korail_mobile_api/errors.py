# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""``h_msg_cd`` → 예외 매핑과 이 패키지의 예외 계층.

.. code-block:: text

    KorailApiError                        모든 실패의 뿌리
    ├── KorailTransportError              HTTP 왕복 자체가 실패
    ├── KorailProtocolError               응답 모양이 프로토콜과 다름
    ├── KorailAuthError                   로그인·세션
    │   ├── KorailSessionExpiredError     P058
    │   └── KorailAuthContinuationRequired  WebView 후속 인증
    ├── KorailDynaPathError               안티매크로 거절(응답 본문의 정수 필드)
    ├── KorailDynaPathRequiredError       DynaPath 가 꺼진 채 요구 경로 호출(전송 전)
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
    └── KorailMutationNotAllowedError     영구 거절된 상태변경(정기권/패스 구매 등)

실패 판정은 ``strResult``(와 ``WRC000288``)이 합니다. 이 매핑은 이미 올라가기로
정해진 예외의 클래스만 고릅니다. 경고 코드를 달고 온 성공 응답은 그대로 성공입니다.

모든 메시지 문자열은 :func:`~korail_mobile_api.redaction.redact_text` 를 통과합니다.
"""

from .redaction import redact_text


class KorailApiError(Exception):
    """이 패키지의 모든 예외의 최상위.

    문자열 인자는 :func:`~korail_mobile_api.redaction.redact_text` 를 거칩니다.

    세 속성은 **여기서 기본값을 보장합니다.** 하위 클래스 절반만 채우던 것이라,
    ``except KorailApiError as error: error.code`` 가 전송 실패나 프로토콜 오류에서
    ``AttributeError`` 로 죽었습니다. 이제 채우지 않는 예외에서는 ``None`` 입니다.
    """

    #: 서버가 준 ``h_msg_cd``. 서버 응답 없이 난 실패는 ``None``.
    code: str | None = None
    #: 서버가 준 ``h_msg_txt``. 없으면 ``None``.
    message: str | None = None
    #: 판정에 쓴 원본 응답. 없으면 ``None``.
    raw: object | None = None

    def __init__(self, *args: object) -> None:
        super().__init__(
            *(
                redact_text(arg) if isinstance(arg, str) else arg
                for arg in args
            )
        )

class _CodeMessagePickle:
    """``(code, message)`` 를 위치 인자로 받는 예외들의 pickle 계약. **믹스인**입니다.

    예외 계층에 클래스를 하나 더 끼우지 않으려고 ``Exception`` 을 상속하지 않습니다 —
    이 모듈 맨 위의 계층 그림이 계속 사실이어야 하고, 잡을 수 있는 이름이 하나
    늘어나서도 안 됩니다. 두 애너테이션은 값을 만들지 않습니다 — 실제 값은 언제나
    :class:`KorailApiError` 가 줍니다. 여기 적는 것은 이 믹스인이 무엇을 요구하는지를
    타입 검사기에 말하기 위해서입니다.

    기반 :class:`KorailApiError` 가 ``self.args`` 에 합쳐진 문자열 하나만 남기므로,
    기본 ``Exception.__reduce__`` 는 ``cls(합쳐진문자열)`` 을 시도하고
    ``TypeError: missing 1 required positional argument: 'message'`` 로 죽습니다.
    ``ProcessPoolExecutor`` 나 Celery 처럼 예외가 프로세스 경계를 넘는 경로에서
    원래 예외 대신 그 ``TypeError`` 가 올라오던 자리입니다. botocore 가
    ``ClientError.__reduce__`` 로 푼 것과 같은 방법입니다.
    """

    code: str | None
    message: str | None

    def __reduce__(self) -> tuple[object, ...]:
        return (self.__class__, (self.code, self.message), dict(self.__dict__))


class KorailTransportError(KorailApiError):
    """HTTP 왕복이 실패해 앱 수준 응답을 파싱하지 못한 경우.

    읽기라면 재시도 가능. 상태변경이라면 요청이 서버에 닿았는지 알 수 없으므로
    예약목록·승차권목록으로 결과를 먼저 확인해야 합니다.
    """


class KorailProtocolError(KorailApiError):
    """응답이 JSON 이 아니거나 봉투 필드(``h_msg_cd``/``h_msg_txt``/``strResult``)가
    빠졌거나 타입이 다른 경우. 재시도해도 같은 응답이 옵니다.

    **전송 전 로컬 검증에도 씁니다.** 요청을 만들 수 없는 입력 — 등록되지 않은
    라우트, 빌더가 만들 수 없는 폼 모양, 빈 대기열 키 — 은 서버에 닿기 전에 이
    예외로 거절됩니다. 그쪽도 "재시도해도 같다"는 성질은 같고, 무엇보다 이
    패키지의 실패는 전부 :class:`KorailApiError` 아래에 있어야 합니다. 맨
    ``ValueError`` 를 올리면 ``except KorailApiError`` 로 받는 호출자를 그냥
    통과합니다.
    """


class KorailAuthError(KorailApiError):
    """로그인 실패 또는 세션 없이 인증 필요 메서드 호출.

    ``code`` 는 서버가 준 ``h_msg_cd`` 입니다. 로그인 요청이 서버 실패를 받았을 때
    채워지고, 그 실패가 :class:`KorailAppError` 였다면 원래 예외가 ``__cause__`` 에
    남습니다. 서버 응답 없이 난 실패(세션 없음, 기기 쪽 인증 등)는 ``None`` 입니다.
    """

    def __init__(self, *args: object, code: str | None = None) -> None:
        super().__init__(*args)
        self.code = code


class KorailSessionExpiredError(_CodeMessagePickle, KorailAuthError):
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
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'P058'}: "
            f"{redact_text(message or 'KORAIL session expired')}",
            code=code,
        )


class KorailDynaPathError(KorailApiError):
    """DynaPath 계층이 요청을 거절 — 안티매크로.

    ``h_msg_cd`` 도 응답 헤더도 아니라 **응답 본문**의 정수 필드로 옵니다 —
    HTTP 상태와 무관하게, :data:`~korail_mobile_api.http._DYNAPATH_BLOCK_CODES`
    에 속하는 값이면 이 예외입니다
    (``analysis/jadx/sources/com/korail/talk/network/interceptor/DynaPathInterceptor.java:97-124``).
    그 정수가 담긴 JSON 필드 이름 자체는 AppSuit 로 난독화돼 PROTECTED 이므로,
    :mod:`~korail_mobile_api.http` 는 이름을 추측하는 대신 응답 본문의 모든
    최상위 값을 훑어 판정합니다 — 자세한 근거는 그 모듈의
    ``_dynapath_block_payload`` 독스트링을 참고하십시오. 예전에는 (틀리게)
    ``DynaPath-Result`` 라는 응답 헤더를 봤습니다 — 그런 헤더는 7.0.6 어디에도
    없습니다.
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        raw: object | None = None,
    ) -> None:
        self.raw = raw
        super().__init__(message or "KORAIL DynaPath request rejected")


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

    def __reduce__(self) -> tuple[object, ...]:
        # Same contract as _ReducibleCodeMessage, different positional pair.
        return (
            self.__class__,
            (self.redirect_url, self.post_data),
            dict(self.__dict__),
        )


def _code_message(code: str | None, message: str | None) -> str:
    """The base class's redaction of the joined string alone is not enough:
    a code that is itself a sensitive key name ("pnrNo: ...") would take the
    message's first word as its value, so the message goes in pre-redacted.
    :class:`KorailSessionExpiredError` does the same inline, with different defaults and no strip.
    """
    return f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip()


class KorailAppError(_CodeMessagePickle, KorailApiError):
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
        super().__init__(_code_message(code, message))


class KorailNoResultsError(KorailAppError):
    """요청은 이해됐고 맞는 것이 없었습니다.

    ``WRG000000``/``P114`` — APK 확인. 빈 화면 상태로 처리됨
    (``BaseActivity.java:326-337`` ``setErrorMsgCdNotShowDialog``,
    ``TicketListActivity.java:1393``).

    ``P100``/``WRT300005`` — 이전엔 "APK 0건, 실서버 관측만"이었으나, AppSuit 가
    건드리지 않는 평문 자산 사전에서 확인됨
    (``analysis/apktool/assets/error_json.json:374`` "검색된 데이터가 없습니다.",
    ``:5141`` "조회자료가 없습니다.").

    ``ERR000100``/``WRT800083``/``WRG500116`` — 같은 "조회결과 없음" 문구 패턴을
    그 사전 전수조사로 추가 확인
    (``analysis/apktool/assets/error_json.json:2312`` "조회된 자료가 없습니다.",
    ``:12835`` "조회할 자료가 없습니다.",
    ``:4241`` "스케줄 조회결과가 없습니다(강릉역의 공사착공으로 정동진역까지만
    열차가 운행합니다)").
    """


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 열차 없음, 환승으로는 가능. ``WRD000061``.

    7.0.6 확인: ``TrainScheduleViewModel`` 이 ``responseTrainSchedule()`` 에서
    ``h_msg_cd`` 를 ``WRD000061`` 과 비교해(smali:35513-35521) 확인창을 띄우고
    (:35550-35566, ``R.string.hm_searchtrain_loading_popup2_body``), 확인을
    누르면 ``changeFilterTransfer()``(java:3216-3219) →
    ``updateTrainScheduleFilterData()``(java:11051-11079, 재질의는 :11077)
    를 거쳐 같은 질의를 다시 보냅니다. 이때 바뀌는 전선 필드는
    ``radJobId``(``buildTrainScheduleIn()`` java:3136,3212, DTO 선언은
    ``TrainScheduleIn.java:95``)이지, 예전에 적혀 있던 ``TRANSFER_SQ_NO``
    가 아닙니다 — 그건 ``K4/d.java`` 의 enum 상수 *이름* 이지 전선 키가
    아니었습니다.
    """


class KorailSoldOutError(KorailAppError):
    """재고 소진. ``ERR211161``.

    ``TCSOptionsActivity.java:551``, ``SpecialRoomUpgradeActivity.java:314``.
    ``strings.xml:2043`` = "잔여석이 부족하여 서비스를 제공할 수 없습니다."

    ``IRT010110``/``WRT300001``/``ERR800048`` —
    ``analysis/apktool/assets/error_json.json`` (AppSuit 가 건드리지 않는 평문
    ``h_msg_cd`` → 안내문구 사전) 전수조사로 추가. ``IRT010110`` 은 이 모듈이 전에
    "APK 전체 0건"이라 일부러 뺐던 코드인데, 그 판정 자체가 이 사전을 보지 못해서
    난 오판이었다 — ``:3203`` "잔여석없음". ``WRT300001``/``ERR800048`` 은 같은
    "매진" 문구로 확인(``:5137`` "좌석이 매진되었습니다.", ``:11062`` "할인승차권의
    잔여석이 모두 매진되었습니다.").
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

    ``ERR911501`` — ``ERR911531`` 과 안내문구가 글자 하나까지 같음("개인 고객
    1인당 구매 한도를 초과하였습니다...1일 최대 20석, 열차별 최대 10석")
    (``analysis/apktool/assets/error_json.json:2633``).
    """


class KorailInvalidRequestError(KorailAppError):
    """필드 수준 검증 거부. 입력을 고쳐야 합니다.

    ``WRG200018``, ``WRT100002``, ``WRT100124`` — 이전엔 "APK 0건, 실서버 관측만"
    이었으나, ``analysis/apktool/assets/error_json.json`` (AppSuit 가 건드리지
    않는 평문 ``h_msg_cd`` → 안내문구 사전) 에서도 확인됨
    (``:4194`` "입력값오류(PNR번호)", ``:4600`` "창구번호미입력,미승인창구",
    ``:4625`` "반환번호를 확인해주세요").

    ``WRG200001``~``WRG200020`` (``WRG200018`` 제외 19개) — 같은
    ``WRG2000xx`` 계열이 "입력값오류(필드명)" 동일 패턴으로 그 사전에
    연속 나열되어 있어 함께 확인(``:4177-4196``).
    """


class KorailNotEntitledError(KorailAppError):
    """이 계정에 그 할인·상품 자격이 없습니다. ``ERR299943``.

    이전엔 "APK 0건, 실서버 관측만"이었으나,
    ``analysis/apktool/assets/error_json.json`` (AppSuit 가 건드리지 않는 평문
    ``h_msg_cd`` → 안내문구 사전) 에서 확인됨
    (``:2475`` "예약할인이 지원되지 않습니다").

    ``ERR800049``/``WRC000419``/``WRC800030``/``WRR800058`` — 같은
    "할인·상품 적용대상 아님" 문구 패턴으로 그 사전 전수조사에서 추가 확인
    (``:11063`` "할인승차권 적용 대상이 아닙니다.",
    ``:12013`` "키즈카드 발급 대상이 아닙니다(만 12세이하)",
    ``:12059`` "회원님께서는 해당할인을 이용할 수 있는 대상이 아닙니다.",
    ``:12492`` "현역병할인 적용대상이 아닙니다.").
    """


class KorailServiceUnavailableError(KorailAppError):
    """KORAIL 백엔드 불가 선언. ``SEMGTK``.

    ``BaseActivity.java:608-609``. 앱은 저장된 승차권 화면을 제안합니다.
    """


class KorailAppUpdateRequiredError(KorailAppError):
    """서버가 앱 업데이트를 요구합니다. ``SUPDATE``.

    ``BaseActivity.java:613-619``. Google Play 로 보냄.
    """


class KorailNetFunnelError(_CodeMessagePickle, KorailApiError):
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
        super().__init__(_code_message(code, message))


class KorailQueueRejectedError(KorailNetFunnelError):
    """대기열이 아예 돌려보냄. ``TsBlock``(301) / ``TsIpBlock``(302).

    ``T6/g.java:892-894`` ``isBlocking()``.
    ``TsExpressNumber``(303)는 앱이 성공으로 셉니다(``T6/g.java:909`` ``isSuccess()``).
    """


class KorailMutationNotAllowedError(KorailApiError):
    """이 라이브러리가 스스로 상태변경 요청을 거절했습니다(예: 정기권/패스 구매).

    서버는 관여하지 않았고 아무것도 전송되지 않았습니다.
    """


class KorailDynaPathRequiredError(KorailApiError):
    """DynaPath 가 필요한 경로인데 설정이 꺼져 있습니다.

    :data:`~korail_mobile_api.constants.DYNAPATH_REQUIRED_PATHS` 의 경로(지금은
    ``login.Login`` 하나)는 토큰 없이 부르면 서버가 거절하므로, 설정이 꺼져 있으면
    이 라이브러리가 전송 전에 막습니다. 허용목록
    (:data:`~korail_mobile_api.constants.DYNAPATH_ALLOWLIST_PATHS`)의 나머지 다섯
    경로는 토큰 없이도 나갑니다.
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
# 그것을 고정하던 테스트는 삭제됐다. 아래 목록이 유일한 기록이다.
#
# analysis/apktool/assets/error_json.json — h_msg_cd -> 안내문구 평문 사전. jadx/smali
# 는 대부분 AppSuit 로 코드 문자열을 감추지만, 이 자산 파일은 컴파일 대상이 아니라서
# 그대로 풀린다. 이걸로 "APK 0건, 실서버 관측만"이라 적었던 판정 다수가 틀렸음이
# 드러났다 — 그 판정은 jadx/smali만 훑고 apktool assets 는 보지 않았던 탓이다.
# IRT010110 이 대표 사례: 전에는 아래 "일부러 넣지 않은 것"에 있었으나, 이 사전에
# "잔여석없음"으로 나와서 SOLD_OUT_CODES 로 옮겼다. 근거는 각 프로즌셋 주석 참고.
#
# 일부러 넣지 않은 것:
#   "MACRO"    이 앱의 안티매크로는 응답 본문의 정수 필드(KorailDynaPathError).
#              error_json.json 전수조사에도 없음 — 재확인.
#   S198       MaaS 전용(BaseActivity.java:621). 이 라이브러리가 구현하지 않는 표면.
#              error_json.json: "품절된 상품이 있어 결제를 진행할 수 없습니다.
#              확인을 누르시면 품절된 상품이 장바구니에서 자동으로 삭제됩니다." —
#              장바구니(MaaS) 문맥이라는 기존 판단과 일치, 재확인만 되고 번복은 없음.
#   ERT800077  앱이 재시도를 권하나 이 라이브러리에 재시도 로직이 없다.
#              error_json.json 전수조사에도 없음 — 재확인.
# ---------------------------------------------------------------------------

#: 빈 결과. ``WRG000000``/``P114`` APK 확인, ``P100``/``WRT300005`` 는
#: error_json.json 에서도 확인(:374,5141). ``ERR000100``/``WRT800083``/
#: ``WRG500116`` 은 같은 "조회결과 없음" 패턴으로 그 사전 전수조사에서 추가.
NO_RESULT_CODES = frozenset({
    "WRG000000", "P114", "P100", "WRT300005",
    "ERR000100", "WRT800083", "WRG500116",
})

#: 직통 없음 → 환승 검색. 7.0.6 확인
#: (``TrainScheduleViewModel.smali:35513-35521``, ``h_msg_cd`` 를 이 코드와
#: 비교; ``error_json.json:4051`` 의 "직통열차는 없지만, 환승으로 조회
#: 가능합니다" 와 대응).
NO_DIRECT_TRAIN_CODE = "WRD000061"

#: 재고 소진. APK 확인. srtgo 의 ``IRT010110`` 은 전엔 0건이라 제외했으나
#: error_json.json:3203 "잔여석없음"으로 확인되어 포함. ``WRT300001``/
#: ``ERR800048`` 도 같은 "매진" 패턴으로 그 사전 전수조사에서 추가(:5137,11062).
SOLD_OUT_CODES = frozenset({"ERR211161", "IRT010110", "WRT300001", "ERR800048"})

#: 좌석 불가. 열차는 아직 예약 가능할 수 있음.
SEAT_UNAVAILABLE_CODES = frozenset({"WRI411345", "ERR911081", "WRT800176"})

#: 예약 거절. 앱은 예약목록으로 보냄. ``ERR911501`` 은 ``ERR911531`` 과 안내문구가
#: 완전히 같아(error_json.json:2633) 그 사전 전수조사에서 추가.
RESERVATION_REFUSED_CODES = frozenset({
    "WRR800029", "ERR911531", "ERR911051", "ERR911501",
})

#: 필드 검증 거부. ``WRG200018``/``WRT100002``/``WRT100124`` 는 전엔 "APK 0건,
#: 실서버 관측만"이었으나 error_json.json 에서 확인됨(:4194,4600,4625).
#: ``WRG200001``~``WRG200020``(``018`` 제외 19개)은 같은 ``WRG2000xx`` 계열이
#: "입력값오류(필드명)" 동일 패턴으로 그 사전에 연속 나열되어 있어 함께 추가
#: (:4177-4196).
INVALID_REQUEST_CODES = frozenset({
    "WRG200018", "WRT100002", "WRT100124",
    "WRG200001", "WRG200002", "WRG200003", "WRG200004", "WRG200005",
    "WRG200006", "WRG200007", "WRG200008", "WRG200009", "WRG200010",
    "WRG200011", "WRG200012", "WRG200013", "WRG200014", "WRG200015",
    "WRG200016", "WRG200017", "WRG200019", "WRG200020",
})

#: 자격 없음. ``ERR299943`` 은 전엔 "APK 0건, 실서버 관측만"이었으나
#: error_json.json 에서 확인됨(:2475). ``ERR800049``/``WRC000419``/
#: ``WRC800030``/``WRR800058`` 은 같은 "할인·상품 적용대상 아님" 패턴으로
#: 그 사전 전수조사에서 추가(:11063,12013,12059,12492).
NOT_ENTITLED_CODES = frozenset({
    "ERR299943", "ERR800049", "WRC000419", "WRC800030", "WRR800058",
})

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
