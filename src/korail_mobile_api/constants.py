"""앱 v6.5.0 디컴파일에서 읽은 상수 — 엔드포인트, 기기 기본값, 코드값.

각 값 옆에 APK 근거가 ``파일:줄`` 로 붙어 있습니다.
닫힌 코드 집합은 :class:`StrEnum` 으로 둡니다.
"""

from enum import StrEnum


KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
#: DynaPath ``dm`` 필드 = ``Build.MODEL``(``b/C1229b.java:132``).
#: 특정 기종 대신 일반 문자열로 둡니다. 실제 기기로 고정하려면
#: :func:`~korail_mobile_api.live.build_config_from_env` 를 씁니다.
#: ``st`` 필드는 별도 리터럴 ``"Android"``(``C1229b.java:135``).
KORAIL_DEFAULT_DEVICE_NAME = "Android"
#: DynaPath ``os`` 필드 = ``Build.VERSION.RELEASE``(``b/C1229b.java:128-131``).
#: ``Build.VERSION.SDK_INT`` 와 다릅니다 — SDK 정수는 아래
#: :data:`KORAIL_DEFAULT_ANDROID_SDK_INT`.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "15"
KORAIL_DEFAULT_DEVICE_WIDTH = 1080
KORAIL_DEFAULT_DEVICE_HEIGHT = 2400
#: ``Build.VERSION.SDK_INT``. ``common.code.do`` 의 ``@Field("OSVersion")``
#: (``CommonService.java:32``). 35 = 안드로이드 15 SDK 레벨.
KORAIL_DEFAULT_ANDROID_SDK_INT = 35


def build_dalvik_user_agent(*, os_release: str, device_model: str) -> str:
    """Dalvik User-Agent 를 앱이 보내는 모양으로 만듭니다.

    ``com.korail.talk`` 은 UA 를 하드코딩하지 않습니다. Retrofit v1 을
    ``HttpURLConnection`` 위에서 쓰므로(``ExecuteDao.java:7-11``) 플랫폼 기본
    Dalvik 문자열이 나갑니다. 끝의 ``Build/<id>`` 는 뺐습니다 — 기기 모델과
    맞지 않는 빌드 id 를 지어내면 검증 못 할 주장이 됩니다.
    """
    return f"Dalvik/2.1.0 (Linux; U; Android {os_release}; {device_model})"


#: :func:`build_dalvik_user_agent` 로 **유도된** 기본 User-Agent.
#: Python 패키지 이름이 든 UA 로는 로그인이 거절됩니다.
KORAIL_USER_AGENT = build_dalvik_user_agent(
    os_release=KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    device_model=KORAIL_DEFAULT_DEVICE_NAME,
)

KORAIL_COMMON_CODE_BOOTSTRAP_CODES = (
    "app.display.image",
    "app.menu.railpoint",
    "app.main.popup",
    "app.easyLogin.isShow",
    "app.korail.boss",
    "app.menu.buynow",
    "app.menu.lost112",
    "app.event.easyPay",
    "app.hndy.athn",
    "app.view.visibility",
    "app.menu.biz",
    "app.event.point",
    "app.var.data",
    "app.login.cphd",
    "app.illegal.report",
    "app.holiday.popup",
    "app.MaaS.test",
    "app.limousine.mainMsg",
)

class KorailSeatClass(StrEnum):
    """객실 등급(``txtPsrmClCd`` / ``psrmClCd``).

    ``K4/o.java:7-9``: ``GENERAL("일반실", "1")``, ``SPECIAL("특실", "2")``.
    ``ALL`` 은 검색 와일드카드(``u4/b.java:101``)이지 객실이 아닙니다.
    """

    GENERAL = "1"
    SPECIAL = "2"


class KorailReservationJobType(StrEnum):
    """``txtJobId`` — 예매 동작 종류.

    넷 다 같은 경로(``certification.TicketReservation``,
    ``CertificationService.java:52-54``)로 갑니다.

    * :attr:`IMMEDIATE`(``"1101"``) — 기본(``C5/a.java:59``, ``:118``).
    * :attr:`STANDBY`(``"1102"``) — 예약대기
      (``DirectInquiryActivity.java:434``).
    * :attr:`SEAT_DESIGNATED`(``"1103"``) — 좌석 선택 결과
      (``C5/a.java:143-146``).
    * :attr:`MERGE_STANDING`(``"1202"``) — 입석+좌석
      (``a5/u.java:394-397``, ``DirectInquiryActivity.java:448-451``).
    """

    IMMEDIATE = "1101"
    STANDBY = "1102"
    SEAT_DESIGNATED = "1103"
    MERGE_STANDING = "1202"


#: 예약대기 대상 ``h_wait_rsv_flg`` 값 — " 9"(공백+9).
#: ``smali/U4/a.smali:1250-1290`` 에서 이 리터럴과만 비교하고,
#: ``:1969-1981`` 에서 ``bundle.putBoolean("wait", ...)`` 로 실립니다.
KORAIL_STANDBY_WAIT_FLAG = " 9"

#: 예약대기 확인 메시지 코드.
#: ``ui/inquiry/rir/orr/a.java:222-225``: 이 코드에서만
#: ``ReservationWaitActivity`` 로 넘어감. 실패가 아님(``strResult`` = ``SUCC``).
KORAIL_STANDBY_HOLD_MESSAGE_CODE = "IRR000014"

#: 할인카드(N카드) 최대 구간 수.
#: ``NCard1~3SectionBookingActivity``, ``K4/f.java:5-11`` 에 넷째 없음.
KORAIL_MAX_DISCOUNT_CARD_SECTIONS = 3

#: N카드 할인종류 코드. ``w4/a.java:100`` 이 쓰고 ``t4/a.java:59-61``
#: ``isNCard()`` 이 읽습니다.
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"

#: N카드 예약 ``txtMenuId``. 좌석지정은 ``"A2"``
#: (``SeatAssignBookingActivity.java:159``).
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


#: 예약 최대 승객 수. ``m5/d.java:32-33`` 최소 0·최대 9,
#: ``m5/c.java:250-252`` 합계 상한.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9


# ---------------------------------------------------------------------------
# 환승 — 여정 하나, 구간 둘.
#
# K4/d.java:5-6: DIRECT_SQ_NO("직통","1") / TRANSFER_SQ_NO("환승","2").
# 검색 job id, txtJrnyCnt, txtJrnySqno 씨앗으로 세 가지 일을 합니다.
# S4/O.java:19-21 이 세 자리 0 채움 → 전선에는 "001"/"002".
KORAIL_DIRECT_ITINERARY_CODE = "1"
KORAIL_TRANSFER_ITINERARY_CODE = "2"

# txtJrnyTpCd: K4/e.java:6-7. smali/K4/e.smali:40 → "11", :68 → "14".
# C5/a.java:60: 환승은 두 구간 모두 "14"(배열 길이를 봄).
# smali/C5/a.smali:306-338 에서 확인.
KORAIL_DIRECT_JOURNEY_TYPE_CODE = "11"
KORAIL_TRANSFER_JOURNEY_TYPE_CODE = "14"

# ---------------------------------------------------------------------------
# 병합예약 — 열차 하나를 중간역에서 나눠 앞뒤를 다르게 앉힘.
#
# smali/K4/e.smali:31-55:
#   STANDING_SEAT_1 "병합 선행" "21"
#   STANDING_SEAT_2 "병합 후행" "22"
#
# DirectInquiryActivity.java:576-601 이 만들며:
#   - txtJrnyTpCd{i}: 루프 인덱스 → 1구간="21", 2구간="22"
#   - txtStndFlg: "Y" 고정(:5887-5891)
#   - 2구간 객실등급 = 1구간 복사(:5919-5983)
#   - arvTm 호출 없음 → arvTm_2 키 없음
# txtJrnyCnt="2", txtJobId="1101", txtJrnySqno="001"/"002".
KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE = "21"
KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE = "22"

#: 병합 대상 판정 ``h_yms_apl_flg`` — 객실별.
#: ``S4/J.java:61-63``: 일반실 ``{"A","G"}``, 특실 ``{"A","S"}``.
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}

#: 예약 최대 구간 수 = 2.
#: ``OSeat.java:32-35``, ``OSrcar.java:21-30`` 은 ``i==1`` 분기만,
#: ``ReservationRequest.java:114-117`` 도 두 좌석만 읽음.
#: ``a5/k.java:108-110``, ``a5/k.java:156-170``: ``new Bundle[2]``.
KORAIL_MAX_JOURNEY_LEGS = 2

# ---------------------------------------------------------------------------
# NetFunnel — 가상 대기열. 호스트가 따로.
#
# KTApplication.java:79-85:
#   setProtocol("https"), setHost("nf.letskorail.com"), setPort(443),
#   setServiceID("service_1"), setActionID("act_8"), setTimeout(3).
#
# T6/h.java:31: path = "ts.wseq".
# U6/c.java:26-33 이 setPath 로 넘겨 URL = https://nf.letskorail.com/ts.wseq.
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
#: 대기열 타임아웃(초). ``KTApplication.java:85``: ``setTimeout(3)``.
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0


class KorailNetFunnelAction(StrEnum):
    """대기열 액션 id(``K4/g.java:43-51``).

    ``act_8``/``act_8_2`` 는 둘 다 열차조회지만 서버가 따로 계량합니다.
    여덟 중 여섯만 APK 에 호출 지점이 있습니다.
    """

    #: 일반 조회. SDK 기본값(``KTApplication.java:84``).
    INQUIRY = "act_8"
    #: 성수기 조회(``b5/c.java:439``, ``MainBookingActivity.java:749``).
    PEAK_SEASON_INQUIRY = "act_8_2"
    #: 상품 조회(``b5/c.java:439``).
    PRODUCT = "act_6"
    #: 예약(``DirectInquiryActivity.java:442``, :469, :499).
    RESERVE = "act_14"
    #: 결제(``B6/AbstractC1269e.java:1046``, ``B6/C1270f.java:232``).
    PAY = "act_18"
    #: 예약목록(``ReservedTicketActivity.java:553``).
    RESERVED = "act_21"
    #: 환불(``K4/g.java:47``). APK 에서 참조 없음 — 게이트 미사용.
    REFUND = "act_22"
    #: 테스트(``K4/g.java:50``). 참조 없음.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """대기열 요청 종류(``T6/c.java:6-11``).

    SRT 의 ``netfunnel.js`` 와 같은 표 — 같은 STCLab NetFunnel SDK.
    """

    CHK_ENTER = "5002"
    ALIVE_NOTICE = "5003"
    SET_COMPLETE = "5004"
    GET_TID_CHK_ENTER = "5101"
    INIT = "5105"
    STOP = "5106"


DYNAPATH_HEADER_NAME = "x-dynapath-m-token"
KORAIL_LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
#: DynaPath 토큰 허용 경로(``ExecuteDao.java:34-39``의 배열 그대로).
DYNAPATH_ALLOWLIST_PATHS = frozenset(
    {
        "/classes/com.korail.mobile.certification.TicketReservation",
        "/classes/com.korail.mobile.nonMember.NonMemTicket",
        "/classes/com.korail.mobile.seatMovie.ScheduleView",
        "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial",
        "/classes/com.korail.mobile.trn.prcFare.do",
        KORAIL_LOGIN_PATH,
    }
)
#: 토큰 **없이는 거절되는** 경로. 끈 설정으로 부르면
#: :class:`~korail_mobile_api.errors.KorailDynaPathRequiredError`.
#: 허용목록보다 좁음 — 검색 등 읽기는 토큰 없이 성공 관측됨,
#: ``login.Login`` 만 거절 관측됨.
DYNAPATH_REQUIRED_PATHS = frozenset({KORAIL_LOGIN_PATH})
