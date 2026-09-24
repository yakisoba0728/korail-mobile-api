# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""패키지 예외 계층과 실패 응답의 h_msg_cd 분류를 제공합니다. 입력 검증의 ValueError 등 모든 오류가 KorailApiError를 상속하는 것은 아닙니다.
classify_app_error는 실패로 판정된 응답의 예외 유형만 고릅니다. 서버 문구·raw의 기록과 노출은 호출자가 관리하십시오."""


class KorailApiError(Exception):
    """패키지의 전송·프로토콜·인증·앱·대기열 오류를 나타냅니다. code·message·raw·parser_raw 는 제공되지 않으면 None 입니다."""

    #: 서버가 준 ``h_msg_cd``. 서버 응답 없이 난 실패는 ``None``.
    code: str | None = None
    #: 서버가 준 ``h_msg_txt``. 없으면 ``None``.
    message: str | None = None
    #: 판정에 쓴 원본 응답. 없으면 ``None``.
    raw: object | None = None
    #: 변경 응답의 모델 파싱이 실패했을 때, 파서가 예외에 붙였던 부분 원본. :attr:`raw` 는 그때 받은 응답 전체로 바뀌므로 이쪽에 옮겨 둡니다. 없으면 ``None``.
    parser_raw: object | None = None


class _CodeMessagePickle:
    """코드와 메시지가 필요한 예외 생성 인자를 직렬화합니다. 예외 계층을 바꾸지 않도록 Exception 을 상속하지 않습니다."""

    code: str | None
    message: str | None

    def __reduce__(self) -> tuple[object, ...]:
        return (self.__class__, (self.code, self.message), dict(self.__dict__))


class KorailTransportError(KorailApiError):
    """HTTP 왕복 실패로 앱 응답을 해석하지 못했음을 나타냅니다.

    읽기라면 재시도 가능. 상태변경이라면 요청이 서버에 닿았는지 알 수 없으므로 예약목록·승차권목록으로 결과를 먼저 확인해야 합니다."""


class KorailProtocolError(KorailApiError):
    """응답 형식 오류 또는 전송 전 입력 검증 실패를 나타냅니다.

    변경 응답의 파싱 실패만으로 서버 처리 여부를 판단할 수 없습니다. 같은 변경을 자동 재전송하지 마십시오."""


class KorailAuthError(KorailApiError):
    """로그인 실패 또는 인증 없는 호출을 나타냅니다.

    ``code`` 는 서버가 준 ``h_msg_cd``, ``raw`` 는 로그인 응답 원문입니다(예: ``WRC000390`` 비밀번호 오류 5회 초과, ``WRR000101``/``S034``
    로그인 정보 오류). 서버 응답 없이 난 실패(세션 없음 등)는 둘 다 ``None`` 입니다."""

    def __init__(
        self, *args: object, code: str | None = None, raw: object | None = None
    ) -> None:
        super().__init__(*args)
        self.code = code
        if raw is not None:
            self.raw = raw


class KorailSessionExpiredError(_CodeMessagePickle, KorailAuthError):
    """FAIL/P058 응답에 따른 세션 만료를 나타냅니다.

    ``strResult`` 가 ``FAIL`` 이거나 CommonOut 봉투에서 누락된 때입니다(누락 기본값이 실패, CommonOut.java:361). 앱은 commonFail() 뒤에 보호된
    4바이트 코드를 비교합니다(CommonOut.java:426-438). P058 과는 길이만 맞으며 로그인 안내 근거는 assets/error_json.json:334, 봉투 판정은
    http.parse_base_response 를 따릅니다."""

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
    """응답 본문에서 DynaPath 차단 정수 코드를 감지했음을 나타냅니다.

    앱 근거: DynaPathInterceptor.java:97-124. 키가 보호돼 이 구현은 모든 최상위 값을 검사합니다. 정확한 검사 범위와 한계는
    http._dynapath_block_payload 참고. 토큰 송신 여부를 뜻하지는 않습니다."""

    def __init__(
        self,
        message: str | None = None,
        *,
        raw: object | None = None,
    ) -> None:
        self.raw = raw
        super().__init__(message or "KORAIL DynaPath request rejected")


class KorailAuthContinuationRequired(KorailAuthError):
    """로그인을 완료하려면 웹 화면에서 후속 조치가 필요함을 나타냅니다.

    7.0.6 은 이 두 코드에서만 ``strRedirectUrl`` 웹 화면을 엽니다(``LoginViewModel.java:1390-1520``). 서버가 준
    :attr:`redirect_url`(없으면 ``""``)과 원문 :attr:`raw`, 코드 :attr:`code` 를 싣습니다. 이 라이브러리는 그 화면을 열거나 결과를 이어 받지 않습니다
    — 조치 후 다시 로그인하십시오."""

    def __init__(self, redirect_url: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.raw = raw
        code = raw.get("h_msg_cd") if isinstance(raw, dict) else None
        super().__init__(
            "KORAIL login requires a web step (dormant account or password change)",
            code=code if isinstance(code, str) else None,
        )

    def __reduce__(self) -> tuple[object, ...]:
        # 생성자 인자를 보존하는 이유는 _CodeMessagePickle 참고.
        return (self.__class__, (self.redirect_url,), dict(self.__dict__))


def _code_message(code: str | None, message: str | None) -> str:
    return f"{code or 'UNKNOWN'}: {message or ''}".strip()


class KorailAppError(_CodeMessagePickle, KorailApiError):
    """실패로 판정된 서버 응답의 앱 수준 오류를 나타냅니다. 알려지지 않은 h_msg_cd 는 이 클래스 그대로 분류됩니다.

    발생 조건은 http.parse_base_response 를 따릅니다. 앱의 봉투 선언은 CommonOut.java:40-44, 공통 오류 처리는
    ScreenViewModel.java:1238-1257 입니다. 이 예외 분류표는 라이브러리의 선택입니다."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(_code_message(code, message))


class KorailNoResultsError(KorailAppError):
    """조회 조건에 맞는 결과가 없음을 나타냅니다. 코드별 메시지 근거는 assets/error_json.json 입니다.

    WRG000000/P114:4173,388; P100/WRT300005:374,5141; ERR000100/WRT800083/WRG500116:2312,12835,4241. 메시지 사전만으로
    앱의 화면 전환을 단정하지 않습니다."""


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 열차 결과가 없어 환승 재조회가 필요함을 나타냅니다.

    앱 필터 전환: TrainScheduleViewModel.java:3216-3219,11051-11079; 요청: TrainScheduleIn.java:95.
    TrainScheduleViewModel.smali:35513-35566 은 코드 비교·확인창을 보여 주지만 비교 문자열은 보호돼 WRD000061 평문을 증명하지 않습니다. 메시지는
    assets/error_json.json:4051 참고."""


class KorailSoldOutError(KorailAppError):
    """매진되었거나 잔여 좌석이 없음을 나타냅니다. 메시지 근거: assets/error_json.json.

    ERR211161:2390; IRT010110:3203; WRT300001:5137; ERR800048:11062. 앱의 특정 UI 처리를 재현한다는 뜻은 아닙니다."""


class KorailSeatUnavailableError(KorailAppError):
    """지정 좌석을 이용할 수 없음을 나타냅니다. 다른 좌석의 예약 가능성은 별도입니다.

    메시지 근거: assets/error_json.json:4340(WRI411345). WRT800176 은 7.0.6 근거가 미확인인 분류값입니다."""


class KorailReservationRefusedError(KorailAppError):
    """중복 예약·구매 한도·예약 가능 시간 등에 따른 예약 거절을 나타냅니다. 앱의 화면 이동은 미확인입니다.

    메시지 근거: assets/error_json.json:12465(WRR800029),2642(ERR911531), 2599(ERR911051),2633(ERR911501)."""


class KorailInvalidRequestError(KorailAppError):
    """서버가 입력 필드 검증을 거절했음을 나타냅니다.

    메시지 근거: assets/error_json.json:4194(WRG200018),4600(WRT100002),4625(WRT100124),
    4177-4196(WRG200001~WRG200020)."""


class KorailNotEntitledError(KorailAppError):
    """할인 또는 상품을 이용할 자격이 없음을 나타냅니다.

    메시지 근거: assets/error_json.json:2475(ERR299943),11063(ERR800049),12013(WRC000419),
    12059(WRC800030),12492(WRR800058)."""


class KorailServiceUnavailableError(KorailAppError):
    """서비스·연결 불가 안내로 분류한 응답을 나타냅니다. assets/error_json.json:66 의 저장 승차권 안내가 근거이며 서버 장애만을 확정하지 않습니다."""


class KorailAppUpdateRequiredError(KorailAppError):
    """앱 업데이트를 요구하는 응답을 나타냅니다. 메시지 근거: assets/error_json.json:65. 스토어 이동 동작은 미확인입니다."""


class KorailNetFunnelError(_CodeMessagePickle, KorailApiError):
    """대기열 통과 실패 또는 잘못된 응답 형식을 나타냅니다. 클라이언트 관문에서는 성공 전용 관문의 비성공 종료·통신 오류나 누적 대기 상한 초과 시 API를 보내지 않습니다. 201/202는
    즉시 오류가 아니라 대기 대상이며 키가 비어 있어도 반복합니다. code는 대기열 코드, raw는 제공된 경우의 응답 본문입니다. h_msg_cd를 분류하는 KorailAppError와
    다릅니다."""

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
    """대기열의 요청 차단 또는 IP 차단 응답을 나타냅니다. Netfunnel.java:67-69,114-116 과 com/netfunnel/api/Code.java:31-33 이 근거입니다.

    303 은 SDK isSuccess() 에 포함되지만(Netfunnel.java:102-104), 관문 mode 의 수용 규칙과는 별개입니다."""


class KorailDynaPathRequiredError(KorailApiError):
    """토큰이 필요한 경로를 DynaPath 비활성 상태로 호출했음을 나타냅니다.

    KorailDynaPathError 는 응답 차단 신호이며, 이 오류는 서버 응답을 받았다는 뜻이 아닙니다."""


# 분류는 실패 응답에만 적용합니다. 봉투·메시지 근거는 network/model/CommonOut.java:40-44와
# common/helper/ErrorHelper.java:44-88,90-114입니다. 메시지 사전은 assets/error_json.json이며 파일명 리터럴은 보호돼 있습니다. SUCC의
# IRR000014·IRT800005·WRS800036·IRZ000001/S200·IRT000000/MRT200105·WRR664296은 코드만으로 예외가 아닙니다. WRR664296도 취소 가능한
# 예약을 만들 수 있습니다. 결제 거절은 raise_on_fail=False라 이 분류를 사용하지 않습니다. MACRO는 h_msg_cd가 아닌 응답 본문의 차단 신호입니다. ERT800077 안내와
# 달리 자동 재시도는 하지 않습니다.

#: 빈 결과 분류. 메시지 근거·한계는 KorailNoResultsError 참고.
NO_RESULT_CODES = frozenset({
    "WRG000000", "P114", "P100", "WRT300005",
    "ERR000100", "WRT800083", "WRG500116",
    "IRR800002", "IRT200279", "IRZ000005", "MRT200648", "WRC000008",
    "WRC000256", "WRD000016", "WRS600208", "WRS600209", "WRS600210",
    "WRT100192", "WRT200125", "WRT300003", "WRT800091",
})

#: 직통 없음 분류: KorailNoDirectTrainError 참고. 앱 비교 리터럴과 이 코드의 동일성은 미확인입니다.
NO_DIRECT_TRAIN_CODE = "WRD000061"

#: 재고 소진 분류. 메시지 근거는 KorailSoldOutError 참고. WRG500113/WRG500114 는 error_json.json:4238-4239(왕편·복편)의 매진 문구입니다.
SOLD_OUT_CODES = frozenset({
    "ERR211161", "IRT010110", "WRT300001", "ERR800048",
    "IRT010510", "IRT011010", "IRT011210", "IRT011310", "WRG500113",
    "WRG500114",
    # TicketReservationKt.java:103,135; smali 의 공통 SOLD_OUT 분기.
    "ERI411321", "EAZ000038",
})

#: 좌석 불가 분류. 다른 좌석의 예약 가능성과 메시지 근거는 KorailSeatUnavailableError 참고.
SEAT_UNAVAILABLE_CODES = frozenset({
    "WRI411345", "WRT800176",
    "ERR521128", "WRS200019", "WRS600242", "WRS800009", "WRS900309",
})

#: 예약 거절 분류. ERR911501 문구는 ERR911531 과 같습니다(error_json.json:2633); 앱의 화면 전환은 미확인입니다. 2026-09-21 라이브: 결제 완료 승차권에
#: cancel_unpaid_hold 를 호출하자 ERR800052(예약내역 확인 안내)가 반환됐습니다.
RESERVATION_REFUSED_CODES = frozenset({
    "WRR800029", "ERR911531", "ERR911051", "ERR911501",
    "ERR299920", "ERR299922", "ERR299932", "ERR299933", "ERR299934",
    "ERR299935", "ERR299936", "ERR299937", "ERR299939", "ERR299941",
    "ERR299992", "ERR299993", "ERR521143", "ERR521158", "ERR521185",
    "ERR800052", "ERR911421", "ERR911528", "WRR664254", "WRR800045",
    # TicketReservationKt.java:95-123: LATE/EXIST. ERR911081 은 좌석 불가가 아닌 LATE.
    "ERR911081", "ERR800056", "S-ERR911411", "S021", "WRR664325",
    "WRR700001", "WRX000007",
})

#: 입력 거절 분류. KorailInvalidRequestError 와 error_json.json:4177-4196,11019-11060,11097 이후의 입력값 오류 문구를 근거로 합니다.
INVALID_REQUEST_CODES = frozenset({
    # 2026-09-22 라이브: get_pbp_acceptance_specifications 에 4자리 sale_date 를 주자 SUCC/ERB000001 이 반환됐습니다(자릿수는
    # OriginalTicketReference 참고). SUCC 는 이 코드만으로 예외가 되지 않습니다. 이 집합은 http.parse_base_response 가 실패로 판정한 뒤에만
    # 사용됩니다.
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

#: 자격 없음 분류. 메시지 근거·한계는 KorailNotEntitledError 참고.
NOT_ENTITLED_CODES = frozenset({
    "ERR299943", "ERR800049", "WRC000419", "WRC800030", "WRR800058",
    "MRR000008", "MRT200005", "WRC000107", "WRC000302", "WRC000373",
    "WRC000412", "WRC000446", "WRR664211",
})

#: SEMGTK의 저장 승차권 안내는 analysis/apktool/assets/error_json.json:66을 따릅니다. 앱 분기 리터럴은 보호돼 있으며 서버 장애만을 뜻한다고 단정하지
#: 않습니다.
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

#: SUPDATE의 업데이트 요구 안내는 analysis/apktool/assets/error_json.json:65을 따릅니다. 앱 분기 리터럴은 보호돼 있습니다.
APP_UPDATE_REQUIRED_CODE = "SUPDATE"

#: 세션 만료는 이 매핑보다 앞에서 KorailSessionExpiredError로 처리합니다.
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
    """실패로 판정된 h_msg_cd 에 맞는 예외를 생성하되 직접 raise 하지 않습니다.

    미등록 코드는 KorailAppError. 성공 응답에 임의로 호출하지 마십시오. P058 은 이 분류 전에 KorailSessionExpiredError 로 처리합니다."""
    subclass = _APP_ERROR_BY_CODE.get(code or "", KorailAppError)
    return subclass(code, message, raw=raw)
