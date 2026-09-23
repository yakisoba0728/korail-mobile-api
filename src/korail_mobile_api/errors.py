# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예외 계층과 h_msg_cd 분류.

KorailApiError 는 전송·프로토콜·인증·앱·대기열 오류의 기반 클래스입니다. 입력 검증에서 발생하는 ValueError 등까지 모두 이 계층에 포함되는 것은 아닙니다.
classify_app_error 는 이미 실패로 판정한 응답의 예외 유형만 고릅니다. 서버 문구와 raw 는 마스킹하지 않으므로 기록 책임은 호출자에게 있습니다.
"""


class KorailApiError(Exception):
    """패키지 오류의 기반 클래스. code·message·raw·parser_raw 는 제공되지 않으면 None 입니다."""

    #: 서버가 준 ``h_msg_cd``. 서버 응답 없이 난 실패는 ``None``.
    code: str | None = None
    #: 서버가 준 ``h_msg_txt``. 없으면 ``None``.
    message: str | None = None
    #: 판정에 쓴 원본 응답. 없으면 ``None``.
    raw: object | None = None
    #: 변경 응답의 typed 파싱이 실패했을 때, 파서가 예외에 붙였던 부분 원본. :attr:`raw` 는 그때 받은 응답 전체로 바뀌므로 이쪽에 옮겨 둡니다. 없으면
    #: ``None``.
    parser_raw: object | None = None


class _CodeMessagePickle:
    """두 위치 인자(code, message)를 요구하는 예외의 pickle 복원을 지원합니다.

    Exception.args 의 합쳐진 문자열만으로는 생성자를 다시 부를 수 없어 인자를 별도로 보존합니다. 예외 계층을 바꾸지 않도록 Exception 을 상속하지 않는
    믹스인입니다.
    """

    code: str | None
    message: str | None

    def __reduce__(self) -> tuple[object, ...]:
        return (self.__class__, (self.code, self.message), dict(self.__dict__))


class KorailTransportError(KorailApiError):
    """HTTP 왕복이 실패해 앱 수준 응답을 파싱하지 못한 경우.

    읽기라면 재시도 가능. 상태변경이라면 요청이 서버에 닿았는지 알 수 없으므로 예약목록·승차권목록으로 결과를 먼저 확인해야 합니다.
    """


class KorailProtocolError(KorailApiError):
    """응답 형식 오류 또는 전송 전 입력 검증 실패.

    변경 응답의 파싱 실패만으로 서버 처리 여부를 판단할 수 없습니다. 같은 변경을 자동 재전송하지 마십시오.
    """


class KorailAuthError(KorailApiError):
    """로그인 실패 또는 세션 없이 인증 필요 메서드 호출.

    ``code`` 는 서버가 준 ``h_msg_cd``, ``raw`` 는 로그인 응답 원문입니다(예: ``WRC000390`` 비밀번호 오류 5회 초과,
    ``WRR000101``/``S034`` 로그인 정보 오류). 서버 응답 없이 난 실패(세션 없음 등)는 둘 다 ``None`` 입니다.
    """

    def __init__(
        self, *args: object, code: str | None = None, raw: object | None = None
    ) -> None:
        super().__init__(*args)
        self.code = code
        if raw is not None:
            self.raw = raw


class KorailSessionExpiredError(_CodeMessagePickle, KorailAuthError):
    """P058 을 세션 만료로 분류합니다. KorailAppError 가 아니라 KorailAuthError 의 하위입니다.

    메시지 근거: assets/error_json.json:334 의 로그인 화면 이동 안내.
    7.0.6 의 대응 비교 리터럴은 보호돼 화면별 처리와의 동일성은 미확인입니다.
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
    """응답 본문의 차단 정수 코드를 감지한 오류.

    앱 근거: DynaPathInterceptor.java:97-124. 키가 보호돼 이 구현은 모든 최상위 값을 검사합니다. 정확한 검사 범위와 한계는
    http._dynapath_block_payload 참고. 토큰 송신 여부를 뜻하지는 않습니다.
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
    """로그인을 끝내려면 웹 화면에서 조치가 필요합니다 — 휴면 해제(``WRC000116``) 또는 비밀번호 변경(``WRC000420``).

    7.0.6 은 이 두 코드에서만 ``strRedirectUrl`` 웹 화면을 엽니다(``LoginViewModel.java:1390-1520``). 서버가 준
    :attr:`redirect_url`(없으면 ``""``)과 원문 :attr:`raw`, 코드 :attr:`code` 를 싣습니다. 이 라이브러리는 그 화면을
    열거나 결과를 이어 받지 않습니다 — 조치 후 다시 로그인하십시오.
    """

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
    """서버 앱 수준 오류. 알려지지 않은 h_msg_cd 는 이 클래스 그대로 분류됩니다.

    발생 조건은 http.parse_base_response 를 따릅니다. 앱의 봉투 선언은 CommonOut.java:40-44, 공통 오류 처리는
    ScreenViewModel.java:1238-1257 입니다. 이 예외 분류표는 라이브러리의 선택입니다.
    """

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(_code_message(code, message))


class KorailNoResultsError(KorailAppError):
    """조회 결과 없음. 코드별 메시지 근거는 assets/error_json.json 입니다.

    WRG000000/P114:4173,388; P100/WRT300005:374,5141; ERR000100/WRT800083/WRG500116:2312,12835,4241.
    메시지 사전만으로 앱의 화면 전환을 단정하지 않습니다.
    """


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 결과 없음(WRD000061). 환승 조회 가능성이지 환승 결과의 존재 보장은 아닙니다.

    앱의 환승 필터 전환: TrainScheduleViewModel.java:3216-3219,11051-11079; 요청 필드: TrainScheduleIn.java:95. 특정
    오류코드 분기 근거는 TrainScheduleViewModel.smali:35513-35566 에 의존하며 jadx 만으로는 확정하지 않습니다.
    """


class KorailSoldOutError(KorailAppError):
    """매진·잔여석 없음. 메시지 근거: assets/error_json.json.

    ERR211161:2390; IRT010110:3203; WRT300001:5137; ERR800048:11062. 앱의 특정 UI 처리를 재현한다는 뜻은 아닙니다.
    """


class KorailSeatUnavailableError(KorailAppError):
    """지정 좌석 이용 불가. 다른 좌석의 예약 가능성은 별도입니다.

    메시지 근거: assets/error_json.json:4340(WRI411345),2601(ERR911081). WRT800176 은 7.0.6 근거가 미확인인 분류값입니다.
    """


class KorailReservationRefusedError(KorailAppError):
    """중복 예약·구매 한도 등의 예약 거절. 앱의 화면 이동은 미확인입니다.

    메시지 근거: assets/error_json.json:12465(WRR800029),2642(ERR911531), 2599(ERR911051),2633(ERR911501).
    """


class KorailInvalidRequestError(KorailAppError):
    """입력 필드 검증 거절.

    메시지 근거: assets/error_json.json:4194(WRG200018),4600(WRT100002),4625(WRT100124),
    4177-4196(WRG200001~WRG200020).
    """


class KorailNotEntitledError(KorailAppError):
    """할인·상품 대상이 아님.

    메시지 근거: assets/error_json.json:2475(ERR299943),11063(ERR800049),12013(WRC000419),
    12059(WRC800030),12492(WRR800058).
    """


class KorailServiceUnavailableError(KorailAppError):
    """서비스/연결 불가 분류(SEMGTK). assets/error_json.json:66 의 저장 승차권 안내가 근거이며 서버 장애만을 확정하지 않습니다."""


class KorailAppUpdateRequiredError(KorailAppError):
    """앱 업데이트 요구(SUPDATE). 메시지 근거: assets/error_json.json:65. 스토어 이동 동작은 미확인입니다."""


class KorailNetFunnelError(_CodeMessagePickle, KorailApiError):
    """NetFunnel 대기열을 통과하지 못해 KORAIL 요청을 보내지 않았습니다.

    예약·결제·예약내역(앱의 ``mode=0`` 관문)에서 대기열이 200 이 아닌 답을 했거나 대기열 요청 자체가 실패한 경우, 키 없이 대기하라고 한 경우,
    :attr:`~korail_mobile_api.config.KorailConfig.netfunnel_wait_limit` 를 넘긴 경우입니다. ``code`` 는 대기열 응답
    코드(없으면 ``None``), ``raw`` 는 응답 본문입니다.

    :class:`KorailAppError` 가 아닙니다 — ``h_msg_cd`` 를 갖지 않는 별도 호스트의 별도 프로토콜입니다.
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
    """대기열 차단 301/302. Netfunnel.java:67-69,114-116 과 com/netfunnel/api/Code.java:31-33 이 근거입니다.

    303 은 SDK isSuccess() 에 포함되지만(Netfunnel.java:102-104), 관문 mode 의 수용 규칙과는 별개입니다.
    """


class KorailDynaPathRequiredError(KorailApiError):
    """DYNAPATH_REQUIRED_PATHS 를 토큰 비활성 상태로 호출하여 전송 전에 거절됐습니다.

    KorailDynaPathError 는 응답 차단 신호이며, 이 오류는 서버 응답을 받았다는 뜻이 아닙니다.
    """


# ---------------------------------------------------------------------------
# h_msg_cd -> exception mapping
#
# 코드로 가른다. 7.0.6 에는 코드 전체를 한자리에서 가르는 switch 가 없다 —
# 분기는 화면별 ViewModel 로 흩어져 있다. 7.0.6 에서 확인되는
# 것은 (a) 봉투 세 필드의 선언(network/model/CommonOut.java:40-44) 과
# (b) h_msg_cd 를 키로 안내문구를 꺼내 화면 문구를 만드는
# common/helper/ErrorHelper.java(두 오버로드 :44-88, :90-114; assets 에서 JSON
# 을 읽어 :77/:111 에서 optString(code, ...) 하는 것이 전부. 자산 파일 이름
# 리터럴은 AppSuit 로 보호돼 있으나 assets 에 있는 h_msg_cd→문구 JSON 은
# error_json.json 하나뿐이다)뿐이다. "코드로 가른다"는 이 라이브러리의
# 선택이다.
#
# 이 매핑이 해서는 안 되는 일: 이미 올라가기로 정해진 예외를 더 좁히는 것만
# 할 수 있다. 성공에 얹혀 오는, 결코 예외가 되어서는 안 되는 코드:
#   IRR000014, IRT800005, WRS800036, IRZ000001/S200, IRT000000/MRT200105,
#   WRR664296  (strResult=SUCC 와 취소 가능한 PNR 을 달고 온다)
# 이것을 고정하는 테스트는 없다. 위 목록이 유일한 기록이다.
#
# analysis/apktool/assets/error_json.json — h_msg_cd -> 안내문구 평문 사전. jadx/smali
# 는 대부분 AppSuit 로 코드 문자열을 감추지만, 이 자산 파일은 컴파일 대상이 아니라서
# 그대로 풀린다 — jadx/smali 에서 0건인 코드도 여기서는 찾을 수 있다. 근거는 각
# 프로즌셋 주석 참고.
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
#   S198       MaaS 전용. 이 라이브러리가 구현하지 않는 표면이라는 판단은
#              아래 문구가 뒷받침한다.
#              error_json.json:208: "품절된 상품이 있어 결제를 진행할 수 없습니다.
#              확인을 누르시면 품절된 상품이 장바구니에서 자동으로 삭제됩니다." —
#              장바구니(MaaS) 문맥.
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

#: 재고 소진. APK 확인. srtgo 의 ``IRT010110`` 은
#: error_json.json:3203 "잔여석없음"으로 확인. ``WRT300001``/
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

#: 필드 검증 거부. ``WRG200018``/``WRT100002``/``WRT100124`` 는 실서버 관측에
#: 더해 error_json.json 에서 확인됨(:4194,4600,4625).
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

#: 자격 없음. ``ERR299943`` 은 실서버 관측에 더해
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

#: 백엔드 불가. 코드 리터럴은 AppSuit 보호로 jadx/smali 0건. 근거는 평문 자산
#: 사전뿐이다 — ``analysis/apktool/assets/error_json.json:66``
#: "…저장된 승차권화면으로 이동하시겠습니까?".
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

#: 앱 업데이트 요구. 코드 리터럴은 AppSuit 보호로 jadx/smali 0건. 근거는
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
    """실패로 판정된 h_msg_cd 에 맞는 예외를 생성하되 직접 raise 하지 않습니다.

    미등록 코드는 KorailAppError. 성공 응답에 임의로 호출하지 마십시오. P058 은 이 분류 전에 KorailSessionExpiredError 로 처리합니다.
    """
    subclass = _APP_ERROR_BY_CODE.get(code or "", KorailAppError)
    return subclass(code, message, raw=raw)
