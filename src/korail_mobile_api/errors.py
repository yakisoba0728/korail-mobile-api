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
    └── KorailNetFunnelError              대기열(nf.letskorail.com)
        └── KorailQueueRejectedError

실패 판정은 ``strResult``(와 ``WRC000288``)이 합니다. 이 매핑은 이미 올라가기로
정해진 예외의 클래스만 고릅니다. 경고 코드를 달고 온 성공 응답은 그대로 성공입니다.

메시지는 가리지 않습니다. 이 패키지가 만드는 메시지에는 자격증명·세션 값을 넣지
않고, 서버가 준 문구(``h_msg_txt``)는 그대로 둡니다. 로그를 어디에 어떻게 남길지는
호출자가 정합니다.
"""


class KorailApiError(Exception):
    """이 패키지의 모든 예외의 최상위.

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
    #: 변경 응답의 typed 파싱이 실패했을 때, 파서가 예외에 붙였던 부분 원본.
    #: :attr:`raw` 는 그때 받은 응답 전체로 바뀌므로 이쪽에 옮겨 둡니다. 없으면 ``None``.
    parser_raw: object | None = None


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
    """세션 만료. ``P058``.

    ``BaseActivity.java:610`` 을 인용하던 자리입니다. 그 클래스는 7.0.6 에
    없고(앱이 Compose + ViewModel 로 재작성됐습니다), ``P058`` 이라는 문자열도
    jadx/smali 전체에 0건입니다 — 코드 리터럴이 AppSuit 로 보호돼 PROTECTED
    입니다. 7.0.6 에서 남는 근거는 평문 자산 사전 한 줄뿐입니다:
    ``analysis/apktool/assets/error_json.json:334`` 의 ``"P058"`` 값이
    ``location.replace('/korail/com/login.do')`` 만 담은 JavaScript 조각이라,
    서버가 이 코드로 로그인 화면 재진입을 지시한다는 성질까지는 확인됩니다.
    어느 화면이 이걸 세션 만료로 처리하는지는 7.0.6 에서 재확인하지 못했습니다
    — 그 부분은 미출처입니다.

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
            f"{message or 'KORAIL session expired'}",
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

    서버가 준 :attr:`redirect_url`(``strRedirectUrl``)과 로그인 응답 원문
    :attr:`raw` 를 싣습니다. 7.0.6 은 이 뒤를 ``h_msg_cd`` 별 WebView GET 으로
    이어 가는데(``LoginViewModel.java:1390-1443``) 그 URL 의 쿼리 구분자는
    AlienGuard 로 보호돼 재현할 수 없으므로, 이어 가는 방법은 호출자가
    ``redirect_url``/``raw`` 를 보고 정합니다.
    """

    def __init__(self, redirect_url: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.raw = raw
        super().__init__("KORAIL login requires WebView continuation")

    def __reduce__(self) -> tuple[object, ...]:
        # Same contract as _CodeMessagePickle, one positional argument.
        return (self.__class__, (self.redirect_url,), dict(self.__dict__))


def _code_message(code: str | None, message: str | None) -> str:
    return f"{code or 'UNKNOWN'}: {message or ''}".strip()


class KorailAppError(_CodeMessagePickle, KorailApiError):
    """서버가 앱 수준 실패로 답함 — ``h_msg_cd`` 분류의 뿌리.

    ``strResult == "FAIL"`` 이거나 ``h_msg_cd == "WRC000288"`` 일 때 올라갑니다.
    매핑되지 않은 코드는 이 클래스 그대로 옵니다.

    실패 판정은 코드가 아니라 ``strResult`` 가 합니다. 봉투 세 필드의 선언은
    ``analysis/jadx/sources/com/korail/talk/network/model/CommonOut.java:40-44``
    입니다 — ``strResult``/``hMsgCd``/``_hMsgTxt`` 를 가진
    ``abstract class CommonOut`` 이고 응답 DTO 141개가 이걸 상속합니다(:53).

    "앱도 인식하지 못한 ``h_msg_cd`` 는 ``FAIL`` 이 아닌 응답에서 그냥 성공으로
    흘려보낸다"는 서술은 ``BaseActivity.java:629`` 의 ``aVar = null`` 을 근거로
    달고 있었습니다. 7.0.6 에는 그 클래스도, 코드 전체를 한자리에서 가르는
    switch 도 없습니다 — ``h_msg_cd`` 분기는 화면별 ViewModel 로 흩어져 있고
    (``ScreenViewModel.java:1238-1257`` ``networkError()`` 는 전송 계층 오류와
    ``DynaPathBlockedException`` 만 다룹니다), 그래서 "어느 분기에도 걸리지
    않으면 그대로 지나간다"는 성질만 구조적으로 남습니다. 원문 한 줄에
    대응하는 7.0.6 위치는 찾지 못했습니다 — 미출처.
    """

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(_code_message(code, message))


class KorailNoResultsError(KorailAppError):
    """요청은 이해됐고 맞는 것이 없었습니다.

    ``WRG000000``/``P114`` — 평문 자산 사전 확인
    (``analysis/apktool/assets/error_json.json:4173`` "조회 결과가 없습니다.",
    ``:388`` "조회된 승차권이 없습니다…"). "빈 화면 상태로 처리됨"의 근거로
    ``BaseActivity.java:326-337`` ``setErrorMsgCdNotShowDialog`` 와
    ``TicketListActivity.java:1393`` 을 달고 있었으나, 7.0.6 에는 두 클래스도
    그 메서드 이름도 없습니다(basename·DEX 클래스명 검색 0건). 승차권 목록
    화면의 현재 자리는 ``MyTicketBaseViewModel.java:101`` 과
    ``MyTicketDetailViewModel.java:136`` 이지만 거기서 이 두 코드를 확인하지는
    못했습니다 — 코드 리터럴이 AppSuit 로 보호돼 jadx/smali 전체에 0건입니다.
    그러니 "빈 화면"이라는 UI 처리는 7.0.6 미출처이고, 이 분류가 서는 근거는
    위 사전 문구입니다.

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

    세 인용이 모두 틀렸던 자리입니다. ``TCSOptionsActivity.java:551`` 과
    ``SpecialRoomUpgradeActivity.java:314`` 은 7.0.6 에 없는 6.5.0 시절
    클래스입니다(basename·DEX 클래스명 검색 0건). 좌석변경 옵션 화면의 현재
    자리는 ``SelfSeatChangeOptionViewModel.java:68`` 이지만 거기에 이 코드
    리터럴은 없습니다 — ``ERR211161`` 은 jadx/smali 전체에 0건이고 AppSuit
    로 보호됩니다. 그리고 ``strings.xml:2043`` 은 그 문구가 아니라
    ``my_ticket_detail_maas_travel_refund_guide``(MaaS 이용권 환불 위약금과
    영업일 3~5일 처리 안내)입니다. "잔여석이 부족하여 서비스를 제공할 수
    없습니다."라는 문장은 ``analysis/apktool/res/`` 전체에도
    ``analysis/apktool/assets/error_json.json`` 에도 없습니다. ``res/values*/``
    는 16개 디렉터리이지만 ``strings.xml`` 은 ``res/values/`` 하나뿐이고,
    "잔여석"이라는 낱말 자체가 ``res/`` 전체에 0건입니다 — 그 낱말은 사전에만
    나오고(``:3579``/``:4334``/``:4335``/``:11744``) 거기서도 ``ERR211161``
    이 아닌 다른 코드들입니다. 이 코드의 실제 문구는
    ``analysis/apktool/assets/error_json.json:2390`` "고객님께서 요구하신
    열차는 이미 매진되었으므로 다른 열차(시간대)를 선택하여 주시기
    바랍니다."입니다.

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

    * ``WRI411345`` — ``analysis/apktool/assets/error_json.json:4340``
      "요청한 호차 및 좌석번호 예약 불가". 예전엔
      ``SpecialRoomUpgradeActivity.java:312-313`` 을 달고 "자동 좌석 배정
      제안"이라 적었으나, 그 클래스는 7.0.6 에 없고 자동 배정 제안이라는 UI
      동작은 재확인하지 못했습니다 — 그 해석은 미출처입니다.
    * ``ERR911081`` — ``analysis/apktool/assets/error_json.json:2601``
      "좌석선택 예약불가". 예전 인용 ``a5/k.java:215-221`` 은 7.0.6 에 없는
      경로이고, "좌석선택 시간 경과"라는 원인 해석도 그 사전 문구에서는
      나오지 않습니다 — 미출처.
    * ``WRT800176`` — 예전 인용 ``TCSOptionsActivity.java:557`` 은 7.0.6 에
      없습니다. 이 코드는 평문 자산 사전에도 없습니다(``WRT8001xx`` 형제는
      ``error_json.json:12847`` 부터 줄지어 있으나 ``176`` 만 빠져 있습니다).
      7.0.6 근거가 전혀 없고 이 분류는 6.5.0 시절 인용에만 기대고 있습니다 —
      미출처.
    """


class KorailReservationRefusedError(KorailAppError):
    """예약 거절. 앱은 사용자를 기존 예약목록으로 보냅니다.

    ``WRR800029``, ``ERR911531``, ``ERR911051`` — 셋 다 평문 자산 사전에서
    확인됩니다(``analysis/apktool/assets/error_json.json:12465`` "동일한 예약
    내역이 있으니, 기존 예약 건을 취소하거나 발권 후 구매하시기 바랍니다.",
    ``:2642`` "개인 고객 1인당 구매 한도를 초과하였습니다…", ``:2599``
    "전체예약건수가 초과되었습니다."). 예전에 달려 있던 ``c5/a.java:174-177``
    과 ``a5/k.java:208-214`` 은 7.0.6 에 없는 경로이고(세 코드 리터럴도
    jadx/smali 전체에 0건 — AppSuit 보호), 위 "앱은 사용자를 기존 예약목록으로
    보냅니다"라는 UI 동작은 7.0.6 에서 재확인하지 못했습니다 — 그 부분은
    미출처입니다.

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

    ``BaseActivity.java:608-609`` 을 인용하던 자리입니다. 그 클래스는 6.5.0
    시절 이름이고 7.0.6 디컴파일에 없으며(jadx/smali 전수 검색 0건) ``SEMGTK``
    리터럴도 전체 0건(AppSuit 보호)입니다. 즉 "앱이 그때 무엇을 띄우는가"를
    보여 주는 **코드** 근거는 7.0.6 에서 재유도하지 못했습니다 — 미출처.
    다만 안내 문구 자체는 평문 자산 사전에서 확인되고, 그 문구가 "앱은
    저장된 승차권 화면을 제안합니다"를 그대로 뒷받침합니다 —
    ``analysis/apktool/assets/error_json.json:66`` "인터넷 연결상태(WiFi, 3G,
    4G)가 좋지 않습니다.저장된 승차권화면으로 이동하시겠습니까?".
    """


class KorailAppUpdateRequiredError(KorailAppError):
    """서버가 앱 업데이트를 요구합니다. ``SUPDATE``.

    ``BaseActivity.java:613-619`` 을 인용하던 자리입니다. 그 클래스는 7.0.6 에
    없고 ``SUPDATE`` 리터럴도 jadx/smali 전체에 0건(AppSuit 보호)입니다. 코드의
    뜻만 평문 자산 사전에서 확인됩니다 —
    ``analysis/apktool/assets/error_json.json:65`` "최신버전으로 업데이트하신
    후 이용하여 주십시오.". "Google Play 로 보냄"은 7.0.6 에서 확인하지
    못했습니다 — ``market://details`` 도 ``play.google.com/store/apps`` 도
    ``jadx/sources/com/korail/`` 아래와 ``res/values/strings.xml`` 에
    0건입니다. 미출처.
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

    ``T6/g.java:892-894``/``:909`` 를 인용하던 자리입니다. ``T6/g`` 는 6.5.0
    시절 난독화 이름이고 7.0.6 디컴파일에 그 경로가 없습니다 — ``T6`` 최상위
    패키지가 jadx/smali 어디에도 없으므로 철회된 인용입니다. **다만 주장
    자체는 7.0.6 에서 다시 확인됩니다**: NetFunnel SDK 가 난독화되지 않은
    원래 패키지 그대로 들어 있습니다 —
    ``analysis/jadx/sources/com/netfunnel/api/Netfunnel.java:114-116``
    ``EvnetCode.isBlocking()`` 이 ``Block``(301)/``IpBlock``(302)에서만 참이고
    (상수 선언은 ``:67-68``), ``ExpressNumber``(303, 선언 ``:69``)는
    ``:102-104`` ``isSuccess()`` 가 성공으로 셉니다. 위에 쓴
    ``TsBlock``/``TsIpBlock``/``TsExpressNumber`` 라는 이름은 별개 열거형인
    ``analysis/jadx/sources/com/netfunnel/api/Code.java:31-33`` 쪽 철자이고,
    같은 301/302/303 입니다.
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
# 코드로 가른다. 근거로 BaseActivity.java:600-649(과 h_msg_txt 표시는 :625)를
# 달고 있었으나 7.0.6 에는 그 클래스가 없고, 코드 전체를 한자리에서 가르는
# switch 도 없다 — 분기는 화면별 ViewModel 로 흩어져 있다. 7.0.6 에서 확인되는
# 것은 (a) 봉투 세 필드의 선언(network/model/CommonOut.java:40-44) 과
# (b) h_msg_cd 를 키로 안내문구를 꺼내 화면 문구를 만드는
# common/helper/ErrorHelper.java(두 오버로드 :44-88, :90-114; assets 에서 JSON
# 을 읽어 :77/:111 에서 optString(code, ...) 하는 것이 전부. 자산 파일 이름
# 리터럴은 AppSuit 로 보호돼 있으나 assets 에 있는 h_msg_cd→문구 JSON 은
# error_json.json 하나뿐이다)뿐이다. "코드로 가른다"는 이 라이브러리의
# 선택이고, 앱이 한자리에서 그렇게 한다는 원래 주장은 7.0.6 미출처다.
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
# 2026-09-21 체계적 재조사: error_json.json 19,919건 전체를 이 라이브러리가 이미
# 쓰는 전선접두사 15개(ERR/ERT/IRG/IRR/IRT/IRZ/MRR/MRT/WRC/WRD/WRG/WRI/WRR/WRS/WRT
# — src/ 전체에서 실제로 인용된 모든 h_msg_cd 를 뽑아 만든 목록)로 좁혀 5,605건,
# 결제·계좌·은행 안내문 및 "재시도요망"류 범용 문구를 뺀 4,415건으로 다시 좁힌 뒤
# (결제 라우트는 raise_on_fail=False 라 카드 거절 코드는 애초에 이 매핑을 타지
# 않는다 — :meth:`~korail_mobile_api.client.KorailClient.pay_with_card` 참고),
# 기존 여섯 카테고리 패턴과 겹치는 문구·이미 확인된 코드와 같은 숫자 계열(형제
# 코드)을 기준으로 117개를 추가했다. 완전히 새로 보는 전선접두사(WRTP/WRTS/WRTV/
# WRTD/WRDB/ERRB/WRIB/WRSB/WRRB)는 이 라이브러리가 그 계열의 어떤 코드도 확인한
# 적이 없어 제외했다 — 근거는 각 프로즌셋 주석 참고.
#
# 일부러 넣지 않은 것:
#   "MACRO"    이 앱의 안티매크로는 응답 본문의 정수 필드(KorailDynaPathError).
#              error_json.json 전수조사에도 없음 — 재확인.
#   S198       MaaS 전용. BaseActivity.java:621 을 달고 있었으나 7.0.6 에 그
#              클래스가 없어 그 인용은 미출처다. 이 라이브러리가 구현하지
#              않는 표면이라는 판단은 아래 문구가 뒷받침한다.
#              error_json.json:208: "품절된 상품이 있어 결제를 진행할 수 없습니다.
#              확인을 누르시면 품절된 상품이 장바구니에서 자동으로 삭제됩니다." —
#              장바구니(MaaS) 문맥이라는 기존 판단과 일치, 재확인만 되고 번복은 없음.
#   ERT800077  앱이 재시도를 권하나 이 라이브러리에 재시도 로직이 없다.
#              error_json.json 전수조사에도 없음 — 재확인.
# ---------------------------------------------------------------------------

#: 빈 결과. ``WRG000000``/``P114`` APK 확인, ``P100``/``WRT300005`` 는
#: error_json.json 에서도 확인(:374,5141). ``ERR000100``/``WRT800083``/
#: ``WRG500116`` 은 같은 "조회결과 없음" 패턴으로 그 사전 전수조사에서 추가.
#: 2026-09-21 재조사(19,919건 전체를 이 라이브러리가 이미 쓰는 전선접두사
#: ``ERR``/``ERT``/``IRG``/``IRR``/``IRT``/``IRZ``/``MRR``/``MRT``/``WRC``/
#: ``WRD``/``WRG``/``WRI``/``WRR``/``WRS``/``WRT`` 로 좁혀 스캔)로
#: 14개 추가 — 전부 같은 "…이 없습니다" 패턴이고 접두사가 이미 확인된
#: 계열입니다: ``IRR800002``(예약내역), ``IRT200279``(정차역정보),
#: ``IRZ000005``(조회할 자료), ``MRT200648``(조회 결과), ``WRC000008``/
#: ``WRC000256``(변경할/변경된 자료), ``WRD000016``(분할합병순환 정보 —
#: :meth:`~korail_mobile_api.client.KorailClient.get_merge_seats_inquiry`
#: 대상), ``WRS600208``~``WRS600210``(삭제/목록/상세 내역),
#: ``WRT100192``(내일로 발권내역), ``WRT200125``(분실신고접수내역),
#: ``WRT300003``(요구한 승차권 정보 — ``WRT300005`` 형제),
#: ``WRT800091``(검표 등록 자료 — ``WRT800083`` 형제).
NO_RESULT_CODES = frozenset({
    "WRG000000", "P114", "P100", "WRT300005",
    "ERR000100", "WRT800083", "WRG500116",
    "IRR800002", "IRT200279", "IRZ000005", "MRT200648", "WRC000008",
    "WRC000256", "WRD000016", "WRS600208", "WRS600209", "WRS600210",
    "WRT100192", "WRT200125", "WRT300003", "WRT800091",
})

#: 직통 없음 → 환승 검색. 7.0.6 확인
#: (``TrainScheduleViewModel.smali:35513-35521``, ``h_msg_cd`` 를 이 코드와
#: 비교; ``error_json.json:4051`` 의 "직통열차는 없지만, 환승으로 조회
#: 가능합니다" 와 대응).
NO_DIRECT_TRAIN_CODE = "WRD000061"

#: 재고 소진. APK 확인. srtgo 의 ``IRT010110`` 은 전엔 0건이라 제외했으나
#: error_json.json:3203 "잔여석없음"으로 확인되어 포함. ``WRT300001``/
#: ``ERR800048`` 도 같은 "매진" 패턴으로 그 사전 전수조사에서 추가(:5137,11062).
#: 2026-09-21 재조사로 6개 추가: ``IRT010510``/``IRT011010``/
#: ``IRT011210``/``IRT011310`` 은 ``IRT010110`` 과 메시지가 토씨까지
#: 같은 "잔여석없음" 형제(같은 ``IRT01xx10`` 계열). ``WRG500113``/
#: ``WRG500114`` 는 이미 있는 ``WRG500116`` 의 형제로 "…없거나
#: 좌석이 매진되었습니다"(:4238-4239, 왕편/복편 각각).
SOLD_OUT_CODES = frozenset({
    "ERR211161", "IRT010110", "WRT300001", "ERR800048",
    "IRT010510", "IRT011010", "IRT011210", "IRT011310", "WRG500113",
    "WRG500114",
})

#: 좌석 불가. 열차는 아직 예약 가능할 수 있음.
#: 2026-09-21 재조사로 5개 추가 — 전부 "…좌석이 존재하지 않습니다"류:
#: ``ERR521128``(복구좌석), ``WRS200019``/``WRS600242``(복구할 좌석),
#: ``WRS800009``(속성이 변경된 좌석), ``WRS900309``(우대석 남길 호차/좌석).
SEAT_UNAVAILABLE_CODES = frozenset({
    "WRI411345", "ERR911081", "WRT800176",
    "ERR521128", "WRS200019", "WRS600242", "WRS800009", "WRS900309",
})

#: 예약 거절. 앱은 예약목록으로 보냄. ``ERR911501`` 은 ``ERR911531`` 과 안내문구가
#: 완전히 같아(error_json.json:2633) 그 사전 전수조사에서 추가.
#: 2026-09-21 재조사로 20개 추가. ``ERR800052``("예약내역을 확인하신 후
#: 다시 시도해 주시기 바랍니다")는 **라이브로 직접 확인** —
#: 결제 완료된 승차권에
#: :meth:`~korail_mobile_api.client.KorailClient.cancel_unpaid_hold` 를
#: (잘못) 부르자 실서버가 그대로 돌려줬습니다. 나머지는 이미 확인된
#: 계열의 형제: ``ERR2999xx``(``ERR299943`` 형제, 장단기·입석·단체 예약
#: 제한류), ``ERR521143``/``:521158``/``:521185``(``ERR521128`` 형제),
#: ``ERR911421``/``:911528``(``ERR911051``/``:911501``/``:911531`` 형제),
#: ``WRR664254``(``WRR664xxx`` 계열), ``WRR800045``(``WRR800029``/
#: ``:800058`` 형제).
RESERVATION_REFUSED_CODES = frozenset({
    "WRR800029", "ERR911531", "ERR911051", "ERR911501",
    "ERR299920", "ERR299922", "ERR299932", "ERR299933", "ERR299934",
    "ERR299935", "ERR299936", "ERR299937", "ERR299939", "ERR299941",
    "ERR299992", "ERR299993", "ERR521143", "ERR521158", "ERR521185",
    "ERR800052", "ERR911421", "ERR911528", "WRR664254", "WRR800045",
})

#: 필드 검증 거부. ``WRG200018``/``WRT100002``/``WRT100124`` 는 전엔 "APK 0건,
#: 실서버 관측만"이었으나 error_json.json 에서 확인됨(:4194,4600,4625).
#: ``WRG200001``~``WRG200020``(``018`` 제외 19개)은 같은 ``WRG2000xx`` 계열이
#: "입력값오류(필드명)" 동일 패턴으로 그 사전에 연속 나열되어 있어 함께 추가
#: (:4177-4196).
#: 2026-09-21 재조사로 64개 추가. ``ERR8000xx``(33개, :11019-11060)와
#: ``ERR9302xx``(18개, :11097-)는 ``WRG2000xx`` 와 토씨까지 같은
#: "입력값오류(필드명)" 패턴이고, 괄호 안 필드명 다수가 이 라이브러리가
#: 실제로 예약 폼에 싣는 값과 그대로 대응합니다 — 예:
#: ``ERR800001``(동행자수)·``ERR800003``(총승객수)는
#: :class:`~korail_mobile_api.mutation_models.KorailPassengerCounts`,
#: ``ERR800016``/``ERR930310``(객실등급/열차속성)은
#: :func:`~korail_mobile_api.mutation_payloads._journey_fields` 가 보내는
#: ``txtPsrmClCd``/``txtTrnClsfCd``, ``ERR930260``/``:930261``(출발역/
#: 도착역운행순서)은 같은 함수의 ``departure_run_order``/
#: ``arrival_run_order``. 나머지 6개는 개별 확인:
#: ``WRC000063``(입력값오류 입니다), ``WRC000210``/``:000260``/
#: ``:000392``(입력하신 값이 맞지 않음류), ``WRC000370``(입력하신
#: 응모번호), ``WRR664227``(``WRR664xxx`` 계열), ``WRT400191``(입력값오류
#: (객실등급)), ``WRT400235``(영화요금입력값오류), ``WRT400356``(여권번호),
#: ``WRT800053``/``:800074``/``:800075``(휴대폰/국적/이메일).
INVALID_REQUEST_CODES = frozenset({
    # ERB000001 "INPUT 값 검증 도중 오류가 발생했습니다." -- 2026-09-22 라이브
    # 확인: ``get_pbp_acceptance_specifications`` 에 8자리 대신 4자리
    # ``sale_date`` 를 주면 이 코드가 옵니다(자릿수 규칙은
    # ``OriginalTicketReference`` docstring). 서버는 이때 ``strResult`` 를
    # ``SUCC`` 로 주므로 봉투 게이트는 통과하고, 분류만 여기서 걸립니다.
    "ERB000001",
    "WRG200018", "WRT100002", "WRT100124",
    "WRG200001", "WRG200002", "WRG200003", "WRG200004", "WRG200005",
    "WRG200006", "WRG200007", "WRG200008", "WRG200009", "WRG200010",
    "WRG200011", "WRG200012", "WRG200013", "WRG200014", "WRG200015",
    "WRG200016", "WRG200017", "WRG200019", "WRG200020",
    "ERR800001", "ERR800002", "ERR800003", "ERR800004", "ERR800005",
    "ERR800006", "ERR800008", "ERR800009", "ERR800010", "ERR800011",
    "ERR800012", "ERR800014", "ERR800015", "ERR800016", "ERR800017",
    "ERR800018", "ERR800019", "ERR800020", "ERR800021", "ERR800022",
    "ERR800023", "ERR800024", "ERR800025", "ERR800026", "ERR800029",
    "ERR800030", "ERR800031", "ERR800033", "ERR800034", "ERR800035",
    "ERR800036", "ERR800037", "ERR800038", "ERR930224", "ERR930226",
    "ERR930227", "ERR930228", "ERR930250", "ERR930260", "ERR930261",
    "ERR930267", "ERR930268", "ERR930278", "ERR930279", "ERR930280",
    "ERR930292", "ERR930293", "ERR930310", "ERR930312", "ERR930328",
    "ERR930329", "WRC000063", "WRC000210", "WRC000260", "WRC000370",
    "WRC000392", "WRC000436", "WRR664227", "WRT400191", "WRT400235",
    "WRT400356", "WRT800053", "WRT800074", "WRT800075",
})

#: 자격 없음. ``ERR299943`` 은 전엔 "APK 0건, 실서버 관측만"이었으나
#: error_json.json 에서 확인됨(:2475). ``ERR800049``/``WRC000419``/
#: ``WRC800030``/``WRR800058`` 은 같은 "할인·상품 적용대상 아님" 패턴으로
#: 그 사전 전수조사에서 추가(:11063,12013,12059,12492).
#: 2026-09-21 재조사로 8개 추가: ``MRR000008``(특별할인 적용대상 아님),
#: ``MRT200005``(포인트 누적 대상 아님), ``WRC000107``/``:000302``/
#: ``:000373``/``:000412``/``:000446``(``WRC000419`` 형제, "…대상이
#: 아닙니다"류), ``WRR664211``(``WRR664xxx`` 계열).
NOT_ENTITLED_CODES = frozenset({
    "ERR299943", "ERR800049", "WRC000419", "WRC800030", "WRR800058",
    "MRR000008", "MRT200005", "WRC000107", "WRC000302", "WRC000373",
    "WRC000412", "WRC000446", "WRR664211",
})

#: 백엔드 불가. ``BaseActivity.java:608`` 을 달고 있었으나 7.0.6 에 그 클래스가
#: 없다(코드 리터럴도 AppSuit 보호로 jadx/smali 0건). 현재 근거는 평문 자산
#: 사전뿐이다 — ``analysis/apktool/assets/error_json.json:66``
#: "…저장된 승차권화면으로 이동하시겠습니까?".
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

#: 앱 업데이트 요구. ``BaseActivity.java:613`` 을 달고 있었으나 7.0.6 에 그
#: 클래스가 없다(코드 리터럴도 AppSuit 보호로 jadx/smali 0건). 현재 근거는
#: 평문 자산 사전뿐이다 — ``analysis/apktool/assets/error_json.json:65``
#: "최신버전으로 업데이트하신 후 이용하여 주십시오.".
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
