# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예외 분류는 라이브러리 정책이며 알려지지 않은 서버 코드는 KorailAppError로 보존합니다."""


class KorailApiError(Exception):
    """라이브러리가 발생시키는 모든 예외의 기반 클래스입니다.

    ``except KorailApiError``로 라이브러리 예외를 한꺼번에 처리할 수 있습니다. 라이브러리가 이 클래스 자체를 발생시키지는
    않습니다. 아래 속성은 값이 없으면 ``None``입니다."""

    #: 서버 결과 코드(``h_msg_cd``)입니다. 대기열 예외에서는 대기열 응답 코드입니다. 서버나 대기열의 응답 없이 발생한
    #: 예외에서는 ``None``입니다.
    code: str | None = None
    #: 서버 결과 메시지(``h_msg_txt``)입니다. 대기열 예외에서는 라이브러리가 쓴 설명입니다. 없으면 ``None``입니다.
    message: str | None = None
    #: 서버가 보낸 응답 원본입니다. 없으면 ``None``입니다.
    raw: object | None = None
    # 조회·변경 응답의 모델 파싱이 실패하면 raw 는 그때 받은 응답 전체로 바뀌므로, 파서가 예외에 붙였던 부분 원본을 이쪽에
    # 옮겨 둡니다(client._parse_mutation_response, _parsing._preserve_read_raw).
    #: 응답 모델을 읽다가 실패했을 때 파서가 읽던 부분 원본입니다. 이때 ``raw``에는 받은 응답 전체가 들어 있습니다.
    #: 없으면 ``None``입니다.
    parser_raw: object | None = None


class _CodeMessagePickle:
    """예외 계층을 바꾸지 않도록 Exception 을 상속하지 않습니다."""

    code: str | None
    message: str | None

    def __reduce__(self) -> tuple[object, ...]:
        return (self.__class__, (self.code, self.message), dict(self.__dict__))


class KorailTransportError(KorailApiError):
    """네트워크 오류로 응답을 받지 못했거나, 서버가 2xx가 아닌 HTTP 상태로 응답했음을 나타냅니다.

    리다이렉트는 따라가지 않으므로 3xx 응답도 이 예외가 됩니다. HTTP 상태 오류이면 ``raw``에 응답 본문이 들어 있고,
    네트워크 오류이면 원래의 ``httpx`` 예외가 ``__cause__``에 들어 있습니다. 상태 변경 메서드에서 발생했다면 요청이 서버에
    닿았는지 알 수 없으므로, 다시 호출하기 전에 예약 목록이나 승차권 목록으로 결과를 확인하세요."""


class KorailProtocolError(KorailApiError):
    """응답을 읽을 수 없거나 요청 전 입력 검사에 실패했음을 나타냅니다.

    응답이 JSON 객체가 아니거나 필수 값이 없을 때, 닫힌 클라이언트로 요청하려 할 때도 발생합니다. 요청 전 입력 검사에서
    발생했다면 요청은 보내지 않은 것입니다. 상태 변경 메서드가 응답을 읽지 못해 발생했다면 서버에서는 처리됐을 수
    있으므로, 다시 호출하기 전에 결과를 확인하세요."""


class KorailAuthError(KorailApiError):
    """로그인에 실패했거나, 로그인이 필요한 메서드를 로그인하지 않고 호출했음을 나타냅니다.

    로그인에 실패하면 ``code``에 로그인 응답의 결과 코드가, ``raw``에 로그인 응답 원본이 들어 있습니다. 로그인하지 않았거나
    세션에 고객번호가 없어 요청 전에 발생한 경우에는 ``code``와 ``raw``가 ``None``이며, 요청은 보내지 않은 것입니다."""

    # 로그인 거절 코드 예(앱 메시지 기준): WRC000390 비밀번호 오류 5회 초과, WRR000101/S034 로그인 정보 오류.

    def __init__(self, *args: object, code: str | None = None, raw: object | None = None) -> None:
        super().__init__(*args)
        self.code = code
        if raw is not None:
            self.raw = raw


class KorailSessionExpiredError(_CodeMessagePickle, KorailAuthError):
    """서버 세션이 만료됐음을 나타냅니다.

    실패 응답의 결과 코드가 ``P058``일 때 발생합니다. 클라이언트는 이 예외를 발생시키기 전에 로컬 세션을 비웁니다.
    계속하려면 ``login``을 다시 호출해 로그인하세요."""

    # 판정: strResult 가 FAIL 이거나 CommonOut 봉투에서 누락된 때입니다(누락 기본값이 실패, CommonOut.java:361). 앱은
    # commonFail() 뒤에 보호된 4바이트 코드를 비교합니다(CommonOut.java:426-438). typed read 는 strResult 누락을
    # KorailProtocolError 로 거절합니다(read_parsers).
    # 로컬 세션 비우기는 KorailClient._run_read 가 맡습니다. search_trains·search_transfer_trains 도 바깥에서 _run_read 로
    # 감쌉니다(tests/test_train_reads.py::test_p058_clears_session_even_on_guidance_path).

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
            f"{code or 'P058'}: {message or 'KORAIL session expired'}",
            code=code,
        )


class KorailDynaPathError(KorailApiError):
    """DynaPath 토큰을 붙이는 경로의 응답에서 차단 코드를 감지했음을 나타냅니다.

    HTTP 상태와 봉투보다 먼저 판정하며, ``raw``에 차단 코드가 든 응답이 들어 있습니다. 차단 코드가 들어 있는 응답 필드는
    앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 그래서 응답 최상위의 정수 값을 모두 검사하므로, 다른 필드의 같은
    값도 차단으로 판정할 수 있습니다."""

    # 앱 근거: DynaPathInterceptor.java:97-124. 키가 보호돼 이 구현은 모든 최상위 값을 검사합니다.

    def __init__(
        self,
        message: str | None = None,
        *,
        raw: object | None = None,
    ) -> None:
        self.raw = raw
        super().__init__(message or "KORAIL DynaPath request rejected")


class KorailAuthContinuationRequired(KorailAuthError):
    """로그인을 마치려면 휴면 계정 해제나 비밀번호 변경 같은 웹 단계가 필요함을 나타냅니다.

    로그인 응답의 결과 코드가 ``WRC000116`` 또는 ``WRC000420``일 때 발생합니다. ``redirect_url``에 서버가 준 웹 주소(없으면
    ``""``)가, ``code``와 ``raw``에 결과 코드와 로그인 응답 원본이 들어 있습니다. 라이브러리는 웹 단계를 대신 진행하지
    않습니다."""

    # 7.0.6 은 이 두 코드에서만 strRedirectUrl 웹 화면을 엽니다(LoginViewModel.java:1390-1520). 코드 목록은
    # session.KORAIL_LOGIN_CONTINUATION_CODES 입니다.

    def __init__(self, redirect_url: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.raw = raw
        code = raw.get("h_msg_cd") if isinstance(raw, dict) else None
        super().__init__(
            "KORAIL login requires a web step (dormant account or password change)",
            code=code if isinstance(code, str) else None,
        )

    def __reduce__(self) -> tuple[object, ...]:
        return (self.__class__, (self.redirect_url,), dict(self.__dict__))


def _code_message(code: str | None, message: str | None) -> str:
    return f"{code or 'UNKNOWN'}: {message or ''}".strip()


class KorailAppError(_CodeMessagePickle, KorailApiError):
    """서버가 실패로 응답했음을 나타냅니다.

    결과 코드에 따라 하위 예외로 나뉘며, 어느 하위 예외에도 해당하지 않는 결과 코드는 이 클래스 그대로 발생합니다.
    ``code``와 ``message``에 결과 코드와 결과 메시지가, ``raw``에 응답 원본이 들어 있습니다."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(_code_message(code, message))


class KorailNoResultsError(KorailAppError):
    """조회 조건에 맞는 결과가 없음을 나타냅니다. 결과 코드 ``WRG000000``, ``P100``, ``P114`` 등에서 발생합니다."""

    # 메시지 사전만으로 앱의 화면 전환을 단정하지 않습니다.


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 열차가 없음을 나타냅니다(결과 코드 ``WRD000061``).

    환승 여정은 ``search_transfer_trains``로 조회하세요. ``search_trains_with_transfer_fallback``은 이 예외가 발생했을
    때만 환승 여정을 조회합니다."""

    # 앱 필터 전환: TrainScheduleViewModel.java:3216-3219,11051-11079; 요청: TrainScheduleIn.java:95.


class KorailSoldOutError(KorailAppError):
    """매진됐거나 남은 좌석이 없음을 나타냅니다. 결과 코드 ``ERR211161``, ``WRT300001`` 등에서 발생합니다."""


class KorailSeatUnavailableError(KorailAppError):
    """지정한 좌석을 이용할 수 없음을 나타냅니다. 결과 코드 ``WRI411345`` 등에서 발생합니다."""

    # 메시지 근거: assets/error_json.json:4340(WRI411345).


class KorailReservationRefusedError(KorailAppError):
    """중복 예약, 구매 한도, 예약 가능 시간 등의 이유로 예약이 거절됐음을 나타냅니다.

    결과 코드 ``WRR800029``, ``ERR911531`` 등에서 발생합니다."""

    # 앱의 화면 이동은 미확인입니다.


class KorailInvalidRequestError(KorailAppError):
    """서버가 입력값을 거절했음을 나타냅니다. 결과 코드 ``WRG200018``, ``WRT100002`` 등에서 발생합니다."""

    # 메시지 근거: assets/error_json.json:4194(WRG200018),4600(WRT100002),4625(WRT100124),
    # 4177-4196(WRG200001~WRG200020).


class KorailNotEntitledError(KorailAppError):
    """할인이나 상품을 이용할 자격이 없음을 나타냅니다. 결과 코드 ``ERR299943``, ``WRC000419`` 등에서 발생합니다."""

    # 메시지 근거: assets/error_json.json:2475(ERR299943),11063(ERR800049),12013(WRC000419),
    # 12059(WRC800030),12492(WRR800058).


class KorailServiceUnavailableError(KorailAppError):
    """서비스나 연결을 이용할 수 없다는 안내 응답을 나타냅니다(결과 코드 ``SEMGTK``).

    서버 장애만을 뜻하지는 않습니다. 로그인 응답이 이 결과 코드이면 ``KorailAuthError`` 대신 이 예외가 발생합니다."""

    # assets/error_json.json:66 의 저장 승차권 안내가 근거이며 서버 장애만을 확정하지 않습니다.


class KorailAppUpdateRequiredError(KorailAppError):
    """앱 업데이트를 요구하는 응답을 나타냅니다(결과 코드 ``SUPDATE``).

    로그인 응답이 이 결과 코드이면 ``KorailAuthError`` 대신 이 예외가 발생합니다."""

    # 메시지 근거: assets/error_json.json:65. 스토어 이동 동작은 미확인입니다.


class KorailNetFunnelError(_CodeMessagePickle, KorailApiError):
    """대기열을 통과하지 못해 API 요청을 보내지 않았음을 나타냅니다.

    대기열 서버가 입장 키 없이 기다리라고 답했을 때, ``reserve``·``pay``·``reservation_view`` 관문에서 대기열 서버가
    통과(``200``)로 답하지 않거나 대기열 서버 오류가 났을 때, 누적 대기 시간이 ``netfunnel_wait_limit``를 넘었을 때
    발생합니다. 대기열 응답으로 판정한 경우에는 ``code``에 대기열 응답 코드가, ``raw``에 대기열 응답이 들어 있습니다.
    대기열 서버 오류로 요청을 보내지 않은 경우에는 ``code``와 ``raw``가 ``None``이고 원래 예외가 ``__cause__``에 들어
    있습니다."""

    # 성공 전용 관문(success_only)의 비성공 종료·통신 오류, 입장 키 없는 대기 응답, 누적 대기 상한 초과에서 API 를 보내지
    # 않습니다(netfunnel.KorailNetFunnelClient). 조회 관문(mode=1)의 대기열 오류는 경고 로그만 남기고 요청을 보냅니다.

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
    """대기열 서버가 요청을 차단했음을 나타냅니다(대기열 응답 코드 ``301``, ``302``).

    모든 관문에서 발생하며, API 요청은 보내지 않은 것입니다. ``code``에 대기열 응답 코드가, ``raw``에 대기열 응답이 들어
    있습니다."""

    # 요청 차단 또는 IP 차단 응답입니다. Netfunnel.java:67-69,114-116 과 com/netfunnel/api/Code.java:31-33 이
    # 근거입니다. 303 은 SDK isSuccess() 에 포함되지만(Netfunnel.java:102-104), 관문 mode 의 수용 규칙과는 별개입니다.


class KorailDynaPathRequiredError(KorailApiError):
    """DynaPath를 끈 설정으로 토큰이 필요한 요청(로그인)을 보내려 했음을 나타냅니다.

    요청은 보내지 않습니다. 서버 응답의 차단 신호를 나타내는 ``KorailDynaPathError``와 달리, 이 예외는 서버 응답을 받았다는
    뜻이 아닙니다. 로그인하려면 DynaPath를 켠 설정(기본값)을 쓰세요."""

    # 대상 경로는 constants.DYNAPATH_REQUIRED_PATHS 이며 http.KorailHttpClient._refuse_missing_dynapath 가 거절합니다.


# 분류는 실패 응답에만 적용합니다. 봉투·메시지 근거는 network/model/CommonOut.java:40-44와
# common/helper/ErrorHelper.java:44-88,90-114입니다. 보호 리터럴은 미확인입니다.

#: ``KorailNoResultsError``로 분류하는 결과 코드입니다.
NO_RESULT_CODES = frozenset(
    {
        "WRG000000",
        "P114",
        "P100",
        "WRT300005",
        "ERR000100",
        "WRT800083",
        "WRG500116",
        "IRR800002",
        "IRT200279",
        "IRZ000005",
        "MRT200648",
        "WRC000008",
        "WRC000256",
        "WRD000016",
        "WRS600208",
        "WRS600209",
        "WRS600210",
        "WRT100192",
        "WRT200125",
        "WRT300003",
        "WRT800091",
    }
)

# 앱 비교 리터럴과 이 코드의 동일성은 미확인입니다.
#: ``KorailNoDirectTrainError``로 분류하는 결과 코드입니다.
NO_DIRECT_TRAIN_CODE = "WRD000061"

# WRG500113/WRG500114 는 error_json.json:4238-4239(왕편·복편)의 매진 문구입니다.
#: ``KorailSoldOutError``로 분류하는 결과 코드입니다.
SOLD_OUT_CODES = frozenset(
    {
        "ERR211161",
        "IRT010110",
        "WRT300001",
        "ERR800048",
        "IRT010510",
        "IRT011010",
        "IRT011210",
        "IRT011310",
        "WRG500113",
        "WRG500114",
        # TicketReservationKt.java:103,135; smali 의 공통 SOLD_OUT 분기.
        "ERI411321",
        "EAZ000038",
    }
)

#: ``KorailSeatUnavailableError``로 분류하는 결과 코드입니다.
SEAT_UNAVAILABLE_CODES = frozenset(
    {
        "WRI411345",
        "WRT800176",
        "ERR521128",
        "WRS200019",
        "WRS600242",
        "WRS800009",
        "WRS900309",
    }
)

# ERR911501 문구는 ERR911531 과 같습니다(error_json.json:2633); 앱의 화면 전환은 미확인입니다.
#: ``KorailReservationRefusedError``로 분류하는 결과 코드입니다.
RESERVATION_REFUSED_CODES = frozenset(
    {
        "WRR800029",
        "ERR911531",
        "ERR911051",
        "ERR911501",
        "ERR299920",
        "ERR299922",
        "ERR299932",
        "ERR299933",
        "ERR299934",
        "ERR299935",
        "ERR299936",
        "ERR299937",
        "ERR299939",
        "ERR299941",
        "ERR299992",
        "ERR299993",
        "ERR521143",
        "ERR521158",
        "ERR521185",
        "ERR800052",
        "ERR911421",
        "ERR911528",
        "WRR664254",
        "WRR800045",
        # TicketReservationKt.java:95-123: LATE/EXIST. ERR911081 은 좌석 불가가 아닌 LATE.
        "ERR911081",
        "ERR800056",
        "S-ERR911411",
        "S021",
        "WRR664325",
        "WRR700001",
        "WRX000007",
    }
)

# KorailInvalidRequestError 와 error_json.json:4177-4196,11019-11060,11097 이후의 입력값 오류 문구를 근거로 합니다.
#: ``KorailInvalidRequestError``로 분류하는 결과 코드입니다.
INVALID_REQUEST_CODES = frozenset(
    {
        # SUCC 는 이 코드만으로 예외가 되지 않습니다. 이 집합은 http.parse_base_response 가 실패로 판정한 뒤에만 사용됩니다.
        "ERB000001",
        "WRG200018",
        "WRT100002",
        "WRT100124",
        "WRG200001",
        "WRG200002",
        "WRG200003",
        "WRG200004",
        "WRG200005",
        "WRG200006",
        "WRG200007",
        "WRG200008",
        "WRG200009",
        "WRG200010",
        "WRG200011",
        "WRG200012",
        "WRG200013",
        "WRG200014",
        "WRG200015",
        "WRG200016",
        "WRG200017",
        "WRG200019",
        "WRG200020",
        "ERR800001",
        "ERR800002",
        "ERR800003",
        "ERR800004",
        "ERR800005",
        "ERR800006",
        "ERR800008",
        "ERR800009",
        "ERR800010",
        "ERR800011",
        "ERR800012",
        "ERR800014",
        "ERR800015",
        "ERR800016",
        "ERR800017",
        "ERR800018",
        "ERR800019",
        "ERR800020",
        "ERR800021",
        "ERR800022",
        "ERR800023",
        "ERR800024",
        "ERR800025",
        "ERR800026",
        "ERR800029",
        "ERR800030",
        "ERR800031",
        "ERR800033",
        "ERR800034",
        "ERR800035",
        "ERR800036",
        "ERR800037",
        "ERR800038",
        "ERR930224",
        "ERR930226",
        "ERR930227",
        "ERR930228",
        "ERR930250",
        "ERR930260",
        "ERR930261",
        "ERR930267",
        "ERR930268",
        "ERR930278",
        "ERR930279",
        "ERR930280",
        "ERR930292",
        "ERR930293",
        "ERR930310",
        "ERR930312",
        "ERR930328",
        "ERR930329",
        "WRC000063",
        "WRC000210",
        "WRC000260",
        "WRC000370",
        "WRC000392",
        "WRC000436",
        "WRR664227",
        "WRT400191",
        "WRT400235",
        "WRT400356",
        "WRT800053",
        "WRT800074",
        "WRT800075",
    }
)

#: ``KorailNotEntitledError``로 분류하는 결과 코드입니다.
NOT_ENTITLED_CODES = frozenset(
    {
        "ERR299943",
        "ERR800049",
        "WRC000419",
        "WRC800030",
        "WRR800058",
        "MRR000008",
        "MRT200005",
        "WRC000107",
        "WRC000302",
        "WRC000373",
        "WRC000412",
        "WRC000446",
        "WRR664211",
    }
)

# SEMGTK의 저장 승차권 안내는 analysis/apktool/assets/error_json.json:66을 따릅니다. 앱 분기 리터럴은 보호돼 있으며 서버 장애만을
# 뜻한다고 단정하지 않습니다.
#: ``KorailServiceUnavailableError``로 분류하는 결과 코드입니다. 서버 장애만을 뜻하지는 않습니다.
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

# SUPDATE의 업데이트 요구 안내는 analysis/apktool/assets/error_json.json:65을 따릅니다. 앱 분기 리터럴은 보호돼 있습니다.
#: ``KorailAppUpdateRequiredError``로 분류하는 결과 코드입니다.
APP_UPDATE_REQUIRED_CODE = "SUPDATE"

#: 세션 만료를 나타내는 결과 코드입니다. 실패 응답에서 이 코드가 오면 ``KorailSessionExpiredError``가 발생합니다.
SESSION_EXPIRED_CODE = "P058"

_APP_ERROR_BY_CODE: dict[str, type[KorailAppError]] = {
    **{code: KorailNoResultsError for code in NO_RESULT_CODES},
    NO_DIRECT_TRAIN_CODE: KorailNoDirectTrainError,
    **{code: KorailSoldOutError for code in SOLD_OUT_CODES},
    **{code: KorailSeatUnavailableError for code in SEAT_UNAVAILABLE_CODES},
    **{code: KorailReservationRefusedError for code in RESERVATION_REFUSED_CODES},
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
    """실패 응답의 결과 코드에 맞는 ``KorailAppError`` 또는 그 하위 예외 객체를 만들어 반환합니다. 예외를 발생시키지는 않습니다."""
    subclass = _APP_ERROR_BY_CODE.get(code or "", KorailAppError)
    return subclass(code, message, raw=raw)
