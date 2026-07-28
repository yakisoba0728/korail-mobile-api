"""이 패키지가 올리는 예외 전부와 ``h_msg_cd`` → 예외 매핑.

계층은 아래와 같습니다. 위를 잡으면 아래가 전부 잡힙니다.

.. code-block:: text

    KorailApiError                        모든 실패의 뿌리
    ├── KorailTransportError              HTTP 왕복 자체가 실패
    ├── KorailProtocolError               응답 모양이 프로토콜과 다름
    ├── KorailAuthError                   로그인·세션
    │   ├── KorailSessionExpiredError     P058
    │   └── KorailAuthContinuationRequired  WebView 후속 인증이 남음
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

가장 자주 틀리는 곳이 세션 만료입니다. ``P058`` 은
:class:`KorailSessionExpiredError` 이고 그것은 :class:`KorailAuthError` 이지
:class:`KorailAppError` 가 아니라서 ``except KorailAppError`` 로는 잡히지
않습니다.

실패인지 아닌지는 오직 ``strResult``(와 ``WRC000288``)가 정합니다. 코드는 이미
올라가기로 정해진 예외가 어느 클래스인지만 고르므로, 경고 코드를 달고 온 성공
응답은 그대로 성공입니다. :func:`classify_app_error` 를 참조하면 됩니다.

모든 메시지 문자열은 생성자에서
:func:`~korail_mobile_api.redaction.redact_text` 를 통과하므로 예외를 그대로
로그에 남겨도 카드번호·비밀번호·이름·전화번호가 새지 않습니다.
"""

from .redaction import redact_text


class KorailApiError(Exception):
    """이 패키지가 올리는 모든 예외의 최상위 — 하나로 잡고 싶으면 이것입니다.

    문자열 인자는 :func:`~korail_mobile_api.redaction.redact_text` 를 거쳐
    저장되므로 ``str(exc)`` 에 민감값이 남지 않습니다.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            *(
                redact_text(arg) if isinstance(arg, str) else arg
                for arg in args
            )
        )


class KorailTransportError(KorailApiError):
    """HTTP 왕복이 실패해 앱 수준 응답을 파싱하지도 못한 경우입니다.

    :mod:`httpx` 가 연결·타임아웃으로 던졌거나 응답이 4xx/5xx 였습니다
    (``http.py``). 서버 코드가 없으므로 ``code`` 속성도 없습니다.

    읽기라면 재시도해도 됩니다. 상태변경 요청이라면 요청이 서버에 닿았는지
    알 수 없으므로 그대로 다시 보내지 말고 예약목록·승차권목록으로 결과를
    먼저 확인해야 합니다.
    """


class KorailProtocolError(KorailApiError):
    """응답이 JSON 이 아니거나 봉투 필드가 빠졌거나 타입이 다른 경우입니다.

    ``h_msg_cd``/``h_msg_txt``/``strResult`` 중 하나라도 없거나 문자열이
    아니면 여기서 걸립니다. 파싱 단계의 값 검증(모르는 역코드, 어긋난
    ``h_chg_trn_seq`` 등)도 같은 예외입니다.

    재시도해도 같은 응답이 옵니다. 입력을 고치거나, 서버 응답 모양이 실제로
    바뀐 것이므로 이 패키지를 고쳐야 합니다.
    """


class KorailAuthError(KorailApiError):
    """로그인이 실패했거나 세션 없이 로그인이 필요한 메서드를 불렀습니다.

    :meth:`~korail_mobile_api.client.KorailClient.login` 이 실패했을 때,
    쿠키 없는 성공 응답이 왔을 때, 그리고 계정이 필요한 메서드를 비로그인
    상태로 불렀을 때 올라옵니다. 하위로
    :class:`KorailSessionExpiredError` 와
    :class:`KorailAuthContinuationRequired` 가 있습니다.
    """


class KorailSessionExpiredError(KorailAuthError):
    """세션이 끊겼습니다. ``P058``.

    응답 봉투의 ``h_msg_cd`` 가 ``P058`` 이면 다른 어떤 분류보다 먼저 이것이
    올라갑니다. 읽기 메서드는 이 예외를 만나면 로컬 세션을 버리고 다시
    올리므로, 호출자는
    :meth:`~korail_mobile_api.client.KorailClient.login` 을 다시 부른 뒤 같은
    요청을 반복하면 됩니다. 상태변경 메서드는 세션을 버리지 않으니 직접
    :meth:`~korail_mobile_api.client.KorailClient.clear_session` 을 부르거나
    다시 로그인해야 합니다.

    :class:`KorailAuthError` 의 하위이고 :class:`KorailAppError` 가
    아닙니다. ``h_msg_cd`` 를 달고 오지만 인증 문제이므로 앱 수준 실패
    분류에 넣지 않습니다.

    ``code``/``message``/``raw`` 에 서버 원본이 그대로 담깁니다.
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
    """DynaPath 계층이 요청을 거절했습니다 — 이 앱의 안티매크로 거절입니다.

    지금 다시 보내도 소용없습니다. 속도 제한이 아니라 표시된 것입니다.

    ``h_msg_cd`` 가 아니라 **응답 헤더** 로 옵니다. ``DynaPath-Result`` 값이
    음수면 앱은 본문 ``message`` 만 띄우고 평소의 ``h_msg_cd`` 사다리는 아예
    돌리지 않습니다(``BaseDaoHelper.java:59-86``,
    ``BaseActivity.java:632-634``). 이 패키지도 같은 조건 — 403 + 음수
    ``DynaPath-Result`` + 여섯 개 민감 경로 중 하나 — 에서만 올립니다
    (``ExecuteDao.java:25-47``).

    그러므로 안티매크로를 뜻하는 서버 코드는 존재하지 않습니다. 문자열
    ``MACRO`` 는 이 앱의 서버 코드나 메시지 어디에도 없고, 앱 안의
    ``MACRO`` 는 클라이언트 플래그 ``IS_MACRO_ACTIVE``(``I4/a.java:14``)와
    문자열 자원 ``macro_alert_message``(``strings.xml:996``)뿐입니다.

    로그인 **성공** 응답이 ``notiTpCd`` 로 ``"MC"``/``"MM"``/``"MS"`` 를
    실어 오면 앱은 그 안내 팝업을 띄우지만 로그인은 성공한 것이라
    (``S4/u.java:57-90``) 여기서 아무것도 올리지 않습니다.

    ``raw`` 에 응답 본문이 담깁니다.
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

    로그인 응답이 성공 코드가 아니면서 ``strRedirectUrl`` 을 실어 왔을 때
    올라옵니다. 이 패키지는 WebView 를 띄우지 않으므로 여기서 멈추고,
    :attr:`redirect_url` 과 앱이 그 URL 에 POST 할 :attr:`post_data` 를
    그대로 넘깁니다. 호출자가 브라우저로 그 과정을 마쳐야 합니다.

    같은 예외가 ``client.session.pending`` 에도 남습니다.
    """

    def __init__(self, redirect_url: str, post_data: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.post_data = post_data
        self.raw = raw
        super().__init__("KORAIL login requires WebView continuation")


class KorailAppError(KorailApiError):
    """서버가 앱 수준 실패로 답했습니다 — ``h_msg_cd`` 분류의 뿌리입니다.

    ``strResult == "FAIL"`` 이거나 ``h_msg_cd`` 가 ``WRC000288`` 일 때
    올라갑니다. 아래 하위 클래스는 전부 **세분화** 일 뿐이라
    ``except KorailAppError`` 로 하나도 빠짐없이 잡히고, 매핑되지 않은
    코드는 이 클래스 그대로 옵니다.

    ``code`` 는 서버의 ``h_msg_cd`` 원문, ``message`` 는 ``h_msg_txt``,
    ``raw`` 는 응답 전체입니다. 하위 클래스가 없는 실패도 ``code`` 로 직접
    분기할 수 있습니다.

    실패인지 아닌지를 코드가 정하지는 않습니다. 앱도 인식하지 못한
    ``h_msg_cd`` 는 ``FAIL`` 이 아닌 응답에서 그냥 성공으로 흘려보냅니다
    (``BaseActivity.java:600-649``, :629 의 ``aVar = null``). 그래서
    경고를 달고 온 성공은 여기서도 성공입니다 —
    :class:`KorailNoResultsError` 와 이 파일 아래쪽 매핑 주석을 참조하면
    됩니다.
    """

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip()
        )


class KorailNoResultsError(KorailAppError):
    """요청은 받아들여졌고 맞는 것이 하나도 없었습니다.

    같은 질문을 다시 해도 소용없고 조건을 바꿔야 합니다. 이 서버는 빈 결과를
    빈 목록이 아니라 코드가 실린 ``FAIL`` 봉투로 답하는 엔드포인트가
    여럿입니다.

    ``WRG000000``, ``P114``, ``P100``, ``WRT300005`` 네 코드입니다. 앱도
    이것을 진짜 오류로 보지 않습니다 — ``WRG000000`` 은 네 화면에서
    ``setErrorMsgCdNotShowDialog`` 로 오류 대화상자를 끄고 빈 화면을 그리며
    (``BaseActivity.java:326-337``), ``P114`` 는 "빈 목록 + 안내" 상태로
    성공 경로에서 처리됩니다(``TicketListActivity.java:1393``).

    ``P100``("검색된 데이터가 없습니다.", 빈 예약내역)과
    ``WRT300005``("조회자료가 없습니다.", 빈 승차권목록)는 APK 에 없고 실제
    응답에서만 관측됐습니다. 이 두 코드를 이미 빈 결과로 받아들이도록 선언한
    엔드포인트는 예외 없이 빈 결과를 돌려주므로
    (``read_parsers._validate_envelope`` 의 ``accepted_empty_codes``), 여기
    매핑이 실제로 쓰이는 것은 선언하지 않은 엔드포인트에 같은 코드가 왔을
    때입니다.
    """


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 열차가 없습니다. 다만 환승으로는 갈 수 있습니다. ``WRD000061``.

    직통으로 다시 물어도 소용없고, 환승 검색으로 다시 물어야 합니다 —
    :meth:`~korail_mobile_api.client.KorailClient.search_trains_with_transfer_fallback`
    또는 :meth:`~korail_mobile_api.client.KorailClient.search_transfer_trains`.

    앱의 해석도 그렇습니다. ``DirectInquiryActivity`` 는 이 코드를 일반 오류
    처리보다 먼저 가로채 두 버튼짜리 대화상자를 띄우고(``:614-633``),
    확인을 누르면 **같은 질의** 를 job id 만 ``TRANSFER_SQ_NO`` 로 바꿔
    다시 보냅니다(``:284-296``). 대화상자 뒤로는 빈 열차 목록을 그리므로
    :class:`KorailNoResultsError` 의 하위입니다.
    """


class KorailSoldOutError(KorailAppError):
    """재고가 없습니다. 이 열차는 예약할 수 없습니다. ``ERR211161``.

    이 열차로는 다시 시도해도 소용없고 다른 열차를 골라야 합니다.

    앱은 두 곳에서 이 코드를 서버 문구 대신 자기 문자열로 바꿔 띄웁니다
    (``TCSOptionsActivity.java:551``,
    ``SpecialRoomUpgradeActivity.java:314``). 그 문자열이
    ``tss_dialog_no_left_seat`` = "잔여석이 부족하여 서비스를 제공할 수
    없습니다."(``strings.xml:2043``)이고, 둘 다 버튼이 하나뿐이라 앱이
    내놓는 다음 수가 없다는 뜻입니다.

    srtgo 가 매진 코드로 함께 드는 ``IRT010110`` 은 APK 전체에서 0건이라
    매핑하지 않았습니다. 애초에 앱의 열차 목록은 매진을 코드가 아니라 표시
    문자열로 판단해(``"매진"``/``"좌석부족"``, ``a5/u.java:354``) 예매 버튼
    자체를 막으므로, 매진 열차는 보통 요청되지도 않습니다.
    """


class KorailSeatUnavailableError(KorailAppError):
    """요청한 **좌석** 을 줄 수 없습니다. 열차는 아직 예약 가능할 수 있습니다.

    이 열차를 포기하지 말고 좌석지정 없이 다시 시도하면 됩니다.
    :class:`KorailSoldOutError` 와 구분되며, 앱도 막다른 길 대신 대안을
    제시해 정확히 그 구분을 합니다.

    * ``WRI411345`` — "요청하신 좌석이 이미 판매되었습니다. 시스템에서
      좌석을 자동으로 배정받으시겠습니까?"(``strings.xml:2046``), 두 번째
      버튼이 임의 좌석 배정입니다
      (``SpecialRoomUpgradeActivity.java:312-313``).
    * ``ERR911081`` — "좌석선택 가능 시간이 지났습니다. 자동으로 좌석을
      배정받으시고, 예약을 진행하겠습니까?"(``strings.xml:2047``), 역시 자동
      배정 제안입니다(``a5/k.java:215-221``).
    * ``WRT800176`` — "좌석변경 가능시간이 아닙니다."(``strings.xml:2045``,
      ``TCSOptionsActivity.java:557``).

    좌석을 지정할 수 있는
    :meth:`~korail_mobile_api.client.KorailClient.reserve` 에 직접 걸리는
    이야기입니다. 이 라이브러리는 대신 재시도하지 않습니다 — 다시 보낸
    예약은 중복 예약이 되므로 판단은 호출자 몫입니다.
    """


class KorailReservationRefusedError(KorailAppError):
    """예약이 거절됐고, 앱은 사용자를 기존 예약목록으로 보냅니다.

    ``WRR800029``, ``ERR911531``, ``ERR911051``. 그대로 다시 보내도 소용
    없습니다. 이미 갖고 있는 예약을 먼저 확인하면 됩니다 —
    :meth:`~korail_mobile_api.client.KorailClient.get_reservation_history`.

    아홉 개 예약 호출 지점이 이 세 코드를 함께 등록해 일반 오류 대화상자를
    끄고(``c5/a.java:174-177``, ``c5/b.java:129-132``, ``c5/c.java:128-131``
    외 여섯 곳), 다섯 개 처리기가 서버의 ``h_msg_txt`` 를 그대로 띄운 뒤
    예약목록 화면으로 넘깁니다(``a5/k.java:208-214`` 의 콜백 ``I0`` 가
    ``ReservedTicketActivity`` 를 띄웁니다).

    왜 거절인지는 앱도 말하지 않습니다. ``message`` 에 담긴 서버 설명이
    전부입니다.
    """


class KorailInvalidRequestError(KorailAppError):
    """요청에 실은 필드를 서버가 거부했습니다. 고칠 것은 입력입니다.

    ``WRG200018`` "입력값오류(PNR번호)", ``WRT100002``
    "창구번호미입력,미승인창구", ``WRT100124`` "반환번호를 확인해주세요".
    다시 보내도 소용없고 값을 고쳐야 합니다.

    세 코드 모두 APK 에 0건입니다. 앱 화면으로는 만들 수 없는 값 — 예약이
    없는 계정의 PNR, 실재하지 않는 승차권의 반환번호 — 을 보냈을 때 오는
    필드 수준 검증 응답입니다.
    """


class KorailNotEntitledError(KorailAppError):
    """이 계정에 그 할인·상품 자격이 없습니다. ``ERR299943``.

    "예약할인이 지원되지 않습니다". 같은 계정으로 다시 시도해도 소용없습니다.

    APK 에는 0건이고 서버 쪽 업무 규칙으로만 존재합니다. 청소년 운임 1명
    단독 예약과 1~3급 장애 + 안내견 조합에서 관측됐고, 둘 다 폼은 앱과
    바이트 단위로 같았습니다. 폼이 정상이라는 점에서
    :class:`KorailInvalidRequestError` 와 다릅니다 — 무엇을 보냈느냐가
    아니라 누가 묻느냐로 거절된 것입니다.

    계정이 어떤 자격을 갖고 있는지는
    :meth:`~korail_mobile_api.client.KorailClient.get_korail_point_summary`
    의 ``disability_flag`` 로 짐작할 수 있습니다.
    """


class KorailServiceUnavailableError(KorailAppError):
    """KORAIL 이 서비스 자체를 불가로 선언했습니다. ``SEMGTK``.

    지금 다시 보내도 소용없습니다. 요청이 아니라 백엔드가 내려간 것입니다.

    앱은 다른 어떤 코드보다 먼저 이것을 검사해 오프라인 대체 오류 ``R4.b``
    로 바꾸고(``BaseActivity.java:608-609``), 일반 오류 알림 대신 저장된
    승차권 화면으로 갈지 묻는 두 버튼 대화상자를 띄웁니다(``:298-301``,
    ``:358-366``).
    """


class KorailAppUpdateRequiredError(KorailAppError):
    """서버가 이 클라이언트 버전을 거부하고 앱 업데이트를 요구합니다. ``SUPDATE``.

    간격을 두고 다시 보내도 소용없습니다. 거부당한 것은 요청이 아니라
    클라이언트입니다.

    앱은 이 코드에만 별도 대화상자를 주고 버튼을 누르면 Google Play 로
    보냅니다(``BaseActivity.java:613-619``). 앱을 떠나는 것으로 답하는
    유일한 코드입니다.

    이 예외를 보면 이 패키지가 매 요청에 싣는 ``Version`` 값
    :data:`~korail_mobile_api.constants.KORAIL_API_VERSION` 이 낡았다고
    보면 됩니다.
    """


class KorailNetFunnelError(KorailApiError):
    """NetFunnel 대기열이 거절했거나 오작동했거나 우리를 계속 붙잡았습니다.

    :mod:`korail_mobile_api.netfunnel` 이 통과(200/300)도 대기(201/202)도
    아닌 모든 결과에서 올립니다. 앱에는 없고 이 라이브러리만 두는 두 가지
    상한 — 폴링 횟수와 총 시간 — 을 넘겼을 때도 같은 예외입니다.

    ``code`` 는 대기열 자신의 세 자리 상태값(``T6/a.java``)이고, 응답을
    아예 파싱하지 못했으면 ``None`` 입니다.

    :class:`KorailAppError` 가 **아닙니다**. 여기 오는 것은
    ``smart.letskorail.com`` 이 아니라 다른 호스트의 다른 프로토콜이고
    ``h_msg_cd`` 를 갖지 않습니다.

    이 예외를 본 적 없는 것이 정상입니다. 대기열이 실제로 걸린 관측은
    없습니다 — 이것을 봤다면 서버가 우리에게 계량을 시작했거나,
    :mod:`korail_mobile_api.netfunnel` 이 가정한 응답 모양이 틀린 것입니다.
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
    """대기열이 아예 돌려보냈습니다. ``TsBlock``(301) / ``TsIpBlock``(302).

    지금 다시 보내도 소용없습니다. 줄을 선 것이 아니라 쫓겨난 것입니다.

    앱도 이 둘을 일반 오류와 섞지 않습니다. ``T6/g.d`` 는 차단에만 따로
    ``isBlocking()`` 술어를 두고(``T6/g.java:892-894``) ``Block``/``IpBlock``
    을 별도 상태로 보냅니다. 여기서도 둘 다 예외이되 이 하위 클래스로 올려,
    숫자 코드를 읽지 않고도 "쫓겨났다"와 "대기열이 고장났다"를 가릴 수 있게
    합니다.

    ``TsExpressNumber``(303)는 여기 넣지 않았습니다. 앱이 그것을 성공으로
    치고(``T6/g.java:909``의 ``isSuccess()``), 관측된 적도 없습니다.
    """


class KorailMutationNotAllowedError(KorailApiError):
    """consent 없이 상태변경 요청을 시도했습니다.

    :func:`~korail_mobile_api.consent.require_mutation_consent` 가 올립니다.
    ``MutationConsent`` 를 아예 넘기지 않았거나, 넘긴 것이
    :class:`~korail_mobile_api.consent.MutationConsent` 가 아니거나, 해당
    범주의 ``allow_<범주>`` 가 거짓일 때입니다. 폼을 만들기도 전에 걸리므로
    아무것도 전송되지 않습니다.

    :class:`KorailAppError` 가 아닙니다 — 서버가 아니라 이 라이브러리가
    막은 것입니다. 고치려면 그 범주를 허용한 consent 를 넘기면 됩니다.
    """


class KorailDynaPathRequiredError(KorailApiError):
    """DynaPath 가 필요한 경로인데 설정이 꺼져 있습니다.

    :data:`~korail_mobile_api.constants.DYNAPATH_ALLOWLIST_PATHS` 의 여섯
    경로는 앱이 안티매크로 토큰을 실어 보내는 곳이고, 토큰 없이 부르면 서버가
    거절합니다. 이 라이브러리는 그 거절을 기다리지 않고 전송 전에 막습니다 —
    서버의 거절이 사용자 문구로는 "앱을 최신 버전으로 업데이트하라"로
    위장돼 오기 때문에, 그대로 두면 설정 문제가 버전 문제로 오진됩니다.

    :class:`KorailDynaPathError` 와 다릅니다. 그쪽은 토큰을 보냈는데 서버가
    거절한 것이고, 이쪽은 아직 아무것도 보내지 않았습니다.

    켜려면 ``KorailConfig(enable_dynapath=True)`` 를 넘기고, 실제 단말 값을
    쓰려면 :func:`~korail_mobile_api.live.build_config_from_env` 를 쓰면
    됩니다. 기본값이 꺼져 있는 것은 의도입니다 — 이 토큰은 자동화 탐지를
    우회하는 값이므로, 보낼지 말지는 이 패키지가 대신 정하지 않습니다.
    """


# ---------------------------------------------------------------------------
# h_msg_cd -> exception mapping
#
# 메시지 문구가 아니라 코드로 가른다. 앱이 그렇게 하기 때문이다. 디스패처의
# 모든 분기가 gethMsgCd() 를 리터럴과 비교하고(BaseActivity.java:600-649),
# h_msg_txt 는 부분 문자열로 맞춰 보는 일 없이 그저 화면에 찍기만 한다(:625).
# 앱이 한국어 문구를 실제로 읽는 곳은 열차 목록 하나뿐인데, 거기서 행의 표시
# 상태에 든 "매진"/"좌석부족" 이 예매 버튼을 막는다(a5/u.java:354). 그것은
# 우리가 이미 파싱하는 데이터를 어떻게 그릴지의 문제이지 오류 분류가 아니다.
#
# 이 매핑이 해서는 안 되는 일. 이미 올라가기로 정해진 예외를 더 좁히는 것만
# 할 수 있다. 실패인지는 strResult(와 앱 자신의 WRC000288)가 정하지 코드가
# 정하지 않으며, 앱도 FAIL 이 아닌 응답에 실린 모르는 코드는 그대로 성공으로
# 흘려보낸다(BaseActivity.java:629 의 `aVar = null`). 성공에 얹혀 오는, 결코
# 예외가 되어서는 안 되는 코드가 앱에 가득하다:
#
#   IRR000014  예약대기 접수 -> ReservationWaitActivity 로 이동
#              (ui/inquiry/rir/orr/a.java:223)
#   IRT800005  안내와 함께 예약 성공. 대화상자의 두 분기가 같은 z2(response)
#              연속 처리를 부른다 (ui/inquiry/rir/orr/a.java:142, :71)
#   WRS800036  구간별 안내. 구매는 계속된다
#              (ui/reservation/confirm/activity/DReservationConfirmActivity.java:76)
#   IRZ000001 / S200   로그인 성공 (S4/u.java:131)
#   IRT000000 / MRT200105  업그레이드 견적 수락 (ui/push/SpecialRoomUpgradeActivity.java:55)
#
# WRR664296("KTX/새마을호/ITX-청춘 열차의 경로 및 장애인(4-6급)할인은
# 토/일/공휴일에는 적용되지 않습니다.")은 strResult=SUCC 와 취소 가능한 실제
# PNR 을 달고 온다 -- 성공한 예약에 붙은 경고다. 분류가 새로운 raise 를
# 만들지 않으므로 이 중 어느 것도 여기서 오류가 될 수 없다.
# tests/test_error_classification.py 가 그것을 고정한다.
#
# 일부러 넣지 않은 것:
#   IRT010110  srtgo 의 두 번째 매진 코드(srtgo/srtgo/ktx.py:388). jadx,
#              smali 세 트리, analysis/raw, analysis/splits 전부에서 0건.
#   "MACRO"    srtgo_plus 의 안티매크로 부분 문자열 검사(srtgo/srtgo.py:756).
#              이 앱의 안티매크로 거절은 DynaPath-Result 헤더다 --
#              KorailDynaPathError 참조.
#   S198       앱이 특별 취급하지만 dao_verify_maas_status 에서만 그렇다
#              (BaseActivity.java:621, ui/menu/BasketTicketActivity.java:811).
#              이 라이브러리가 구현하지 않는 MaaS 표면이다. 엔드포인트 하나에
#              한정된 코드를 전역 규칙으로 올리면 나머지 전부에서 오분류된다.
#   ERT800077  "좌석변경 중 문제가 발생하였습니다. 다시 시도해주세요."
#              (TCSOptionsActivity.java:555). 앱 자신의 문구가 재시도를
#              권하는데 이 라이브러리에는 재시도 로직이 없다. 재시도를
#              암시하는 클래스를 주지 않고 밋밋한 KorailAppError 로 둔다.
#   "[3]인증정보에 문제가 있습니다."  좌석 조회를 몰아친 뒤 한 번 관측됐다.
#              h_msg_cd 가 함께 잡히지 않았고 문자열도 APK 에 0건이라 키로
#              삼을 것이 없다. 분류하려면 한국어 문구를 맞춰 봐야 하는데,
#              그것이 바로 이 매핑이 대신하려는 방식이다. 무엇이 이것을
#              부르는지는 확인되지 않았다 -- 속도 제한일 수도, DynaPath 나
#              세션 문제일 수도 있다. 메시지를 그대로 단 밋밋한
#              KorailAppError 로 올라온다.
# ---------------------------------------------------------------------------

#: 요청은 이해됐고 맞는 것이 없었습니다. ``WRG000000``/``P114`` 는 앱이 빈 화면
#: 상태로 다루는 것이 APK 로 확인되고, ``P100``/``WRT300005`` 는 실제 응답에서만
#: 관측됐습니다.
NO_RESULT_CODES = frozenset({"WRG000000", "P114", "P100", "WRT300005"})

#: 직통이 없습니다. 앱은 같은 질의를 환승 검색으로 다시 보냅니다.
NO_DIRECT_TRAIN_CODE = "WRD000061"

#: 재고 소진. APK 확인. srtgo 의 ``IRT010110`` 은 0건이라 넣지 않았습니다.
SOLD_OUT_CODES = frozenset({"ERR211161"})

#: 지정한 좌석은 줄 수 없으나 열차는 아직 예약 가능할 수 있습니다.
SEAT_UNAVAILABLE_CODES = frozenset({"WRI411345", "ERR911081", "WRT800176"})

#: 예약 거절. 앱은 사용자를 기존 예약목록으로 보냅니다.
RESERVATION_REFUSED_CODES = frozenset({"WRR800029", "ERR911531", "ERR911051"})

#: 필드 수준 검증 응답. 실제 응답에서만 관측됐고 APK 에는 0건입니다.
INVALID_REQUEST_CODES = frozenset({"WRG200018", "WRT100002", "WRT100124"})

#: 계정에 자격이 없습니다. 실제 응답에서만 관측됐고 APK 에는 0건입니다.
NOT_ENTITLED_CODES = frozenset({"ERR299943"})

#: 백엔드 불가 선언. 앱은 오프라인 승차권 화면을 제안합니다.
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

#: 이 클라이언트 버전이 거부됐습니다. 앱은 사용자를 Google Play 로 보냅니다.
APP_UPDATE_REQUIRED_CODE = "SUPDATE"

#: 세션 만료. 이 매핑보다 앞에서 :class:`KorailSessionExpiredError` 로
#: 처리됩니다.
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

    올리지 않고 **돌려줍니다**. 각 호출 지점이 자기 ``raise`` 와 자기
    트레이스백을 유지하게 하기 위해서입니다. 모르는 코드나 코드 없음은 밋밋한
    :class:`KorailAppError` 가 되고, 어느 경우든 ``code``/``message``/``raw``
    는 그대로 실립니다.

    이 함수는 실패를 **어느 예외로 부를지** 만 정하고 실패인지 아닌지는 정하지
    않습니다. 이미 :class:`KorailAppError` 를 올리기로 한 자리에서만 불러야
    합니다 — 성공 응답의 코드를 넘기면 서버가 알리지도 않은 실패를 만들어
    내게 됩니다.

    ``P058`` 은 여기서 다루지 않습니다. 이 매핑을 보기 전에
    :class:`KorailSessionExpiredError` 로 처리되며, 그것은
    :class:`KorailAuthError` 이지 :class:`KorailAppError` 가 아닙니다.
    """
    subclass = _APP_ERROR_BY_CODE.get(code or "", KorailAppError)
    return subclass(code, message, raw=raw)
