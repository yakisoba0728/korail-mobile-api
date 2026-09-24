# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""KORAIL 7.0.6 근거가 있는 상수와 라이브러리 기본값을 제공합니다. 평문 선언·@SerialName과 달리 보호 문자열의 바이트 길이는 평문이나 enum 값 배정을 증명하지 않습니다.
미확인 값은 항목별 한계를 따릅니다. 화면 크기·SDK 기본값은 APK 상수가 아닌 device-pull 실기기 기록입니다."""

from enum import StrEnum

KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
#: 토큰 dm 은 Build.MODEL(a/b.java:113-116); 이 기본값은 특정 실기기 모델이 아닙니다. st 는 별도 평문 "Android"(a/b.java:117). 초기화·생성:
#: DynaPathMobileSDK.java:31-71.
KORAIL_DEFAULT_DEVICE_NAME = "Android"
#: os 는 Build.VERSION.RELEASE(a/b.java:109-112), SDK 정수와 다릅니다. 필드명 "os": com/kakao/sdk/common/Constants.java:30.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "15"
#: 실기기 기록: analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:10. 앱은 고정 상수 대신 창 크기를
#: 읽습니다(NetworkService.java:2002,2014). live.build_config_from_env 의 기본 화면 크기도 같은 표본에 맞췄습니다.
KORAIL_DEFAULT_DEVICE_WIDTH = 1440
KORAIL_DEFAULT_DEVICE_HEIGHT = 3120
#: CommonCodeIn.java:91 의 OSVersion 필드. 라우트: NetworkApi.java:315-321. 37 은 앱 상수가 아니라
#: device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:5 의 SDK 값; getprop.txt:1055 도 같은 값이며 release 는
#: summary.tsv:4 의 별도 값입니다.
KORAIL_DEFAULT_ANDROID_SDK_INT = 37


def build_dalvik_user_agent(*, os_release: str, device_model: str) -> str:
    """서버 수용 기록에 근거한 Dalvik 형식의 User-Agent를 만듭니다. 앱 UA 의 재현이라고 단정하지 않습니다.

    7.0.6 은 OkHttp 를 사용하며(NetworkModule.java:55-64), 기본 UA 는 okhttp3/internal/Util.java:87 의 okhttp/4.12.0 입니다.
    실제 송신 UA 는 미확인입니다. 실서버 관측상 Python 패키지 이름 UA 는 로그인 거절, 이 문자열은 수용됐습니다. 기기와 맞지 않는 Build ID 는 만들지 않습니다."""
    return f"Dalvik/2.1.0 (Linux; U; Android {os_release}; {device_model})"


#: :func:`build_dalvik_user_agent` 로 **유도된** 기본 User-Agent. Python 패키지 이름이 든 UA 로는 로그인이 거절됩니다.
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
    """예약할 객실 등급을 나타냅니다. PsrmType.java:19-22 에 GENERAL/SPECIAL 과 psrmClCd 가 있습니다.

    "1"/"2" 배정은 보호돼 미확인입니다. 필드명 근거: TicketReservationInJrny.java:234. ALL 은 이 enum 의 객실 등급이 아닙니다."""

    GENERAL = "1"
    SPECIAL = "2"


class KorailReservationJobType(StrEnum):
    """일반·좌석지정·예약대기·병합 예약 작업을 구분합니다. 공통 라우트: NetworkApi.java:751-753.

    ReservationJobId.java:20-24 의 DEFAULT/WAIT/SEAT/MERGE 등에 대응하나 코드 평문은 보호돼 있습니다.
    TicketReservationType.java:38-42 는 DEFAULT/STAND/FREE 에 같은 DEFAULT job 을 사용합니다. 앱의 병합·대기·결제 화면 분기는 응답 여정종류가
    아니라 요청 txtJobId 를 봅니다 (TrainScheduleViewModel.java:6773-6781). 이 enum 의 숫자 배정은 라이브러리의 관측값입니다."""

    IMMEDIATE = "1101"
    STANDBY = "1102"
    SEAT_DESIGNATED = "1103"
    MERGE_STANDING = "1202"


#: 예약대기 판정값. 앞 공백도 값의 일부입니다. 필드 근거: TrainScheduleOutTrainInfo.java:146,1476. 비교 리터럴은 보호돼 미확인입니다.
KORAIL_STANDBY_WAIT_FLAG = " 9"

#: 예약대기 안내 코드. assets/error_json.json:3181 은 메시지 문구의 근거일 뿐 strResult=SUCC 나 화면 전환 조건을 증명하지 않습니다. 성공 여부는 실제 응답
#: 봉투로 판정합니다.
KORAIL_STANDBY_HOLD_MESSAGE_CODE = "IRR000014"

#: N카드 최대 구간 수는 라이브러리 제한입니다. 7.0.6 의 동일 상한은 미확인입니다.
KORAIL_MAX_DISCOUNT_CARD_SECTIONS = 3

#: N카드 할인코드. ReqDiscount.java:36 / ResDiscount.java:46 에 N_CARD 가 있으나 값은 보호됨. 판정 헬퍼: DiscountHelper.java:818,
#: 호출: TCReservationRequestHelper.java:284. 필드: TicketReservationInPassengerInfo.java:33. "153" 배정 자체는 정적으로
#: 미확인입니다.
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"

#: N카드 예약 메뉴. TicketReservationIn.java:43 의 txtMenuId. ReservationMenuId.java:21-22 는 SEAT_ASSIGN 과 N_CARD 를 별개로
#: 선언합니다. 두 항목의 값은 보호돼 있으므로 모두 "A2" 로 보내는 현재 설정이 앱과 같은지는 미확인입니다.
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


#: 합계 승객 수의 라이브러리 상한. Passengers.java:48 의 MAX_COUNT=9 는 평문입니다. 합계 함수는 Passengers.java:610-616, 요청 필드는
#: TicketReservationIn.java:54. 앱 검증 분기의 상세 처리는 보호돼 있습니다.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9


# 직통·환승 코드. JourneyDefine.java:22-28 의 SequenceNo 값은 보호돼 있습니다. 여정번호 인자는 TrainScheduleOutTrainInfo.java:3683 에서
# 그대로 DTO 로 전달됩니다. 기본값(:1631)·환승 호출(TrainScheduleViewModel.java:2968)도 보호됨. "001"/"002" 는 라이브 수용값이며, 앱의 숫자 포맷팅을
# 확인한 결과가 아닙니다.
KORAIL_DIRECT_ITINERARY_CODE = "1"
KORAIL_TRANSFER_ITINERARY_CODE = "2"

# 여정종류 필드: TicketReservationInJrny.java:230; enum: JourneyDefine.java:87-90. 환승 여부에 따른 분기:
# TrainScheduleOutTrainInfo.java:3674-3683. 환승 호출부는 두 구간에 true 를 전달합니다(TrainScheduleViewModel.java:2952-2968).
# "11"/"14" 평문 배정은 보호돼 있으며 두 구간 "14" 전송은 라이브 수용값입니다.
KORAIL_DIRECT_JOURNEY_TYPE_CODE = "11"
KORAIL_TRANSFER_JOURNEY_TYPE_CODE = "14"

# 병합 홀드 응답의 여정 종류는 선행 "21"·후행 "22" 입니다(JourneyDefine.java:89-90, 평문 보호; 2026-09-21·22 라이브 관측). 요청은 여정을 나누지 않습니다
# — mutation_payloads.build_merge_reservation_form 참고.

#: 객실별 병합 가능 플래그. 필드명: TrainScheduleOutTrainInfo.java:147,1480. 판정 메서드:
#: TrainScheduleOutTrainInfo.java:1500-1552. 비교 리터럴이 보호돼 있어 이 표의 값 배정은 정적으로 미확인입니다.
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}

#: 라이브러리의 최대 구간 수. TicketReservationIn.java:32-54 는 선행·후행 좌석 필드를 한 쌍으로
#: 선언합니다(TicketReservationInSrcarTrailing.java:24-30). 이것은 두 구간 좌석 구성의 근거이며 모든 앱 여정의 하드 상한을 증명하지는 않습니다.
KORAIL_MAX_JOURNEY_LEGS = 2

# NetFunnel 설정·주입은 NetworkConstants.java:80-99와 KorailTalkApplication.java:361-389을 따릅니다.
# PORT=443·RETRY=1·TIMEOUT=3은 평문이며 호스트·프로토콜·액션은 보호돼 있습니다. nf.letskorail.com은 실서버 수용값이며 SDK 기본 호스트와
# 다릅니다(com/netfunnel/api/Property.java:11). ts.wseq·service_1은 SDK 기본값(com/netfunnel/api/Property.java:17-18)이며
# 경로의 /는 URL.java:75-108,126-137을 따릅니다.
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
#: 요청당 제한시간은 3초입니다(NetworkConstants.java:84; KorailTalkApplication.java:387).
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0
#: 재시도는 첫 시도 외 1회입니다(NetworkConstants.java:83; KorailTalkApplication.java:388). SDK는 실패한 시도 시작부터 제한시간을 채운 뒤
#: 재시도합니다 (Netfunnel.java:352-363; com/netfunnel/api/Property.java:16의 wait_retry_=true).
KORAIL_NETFUNNEL_RETRY = 1


class KorailNetFunnelAction(StrEnum):
    """대기열 관문에 사용할 액션 식별자를 나타냅니다. NetworkConstants.java:88-94 에 액션 상수 일곱 개가 있습니다.

    값은 보호돼 있으며 같은 길이의 후보들을 길이만으로 구별할 수 없습니다. 이 enum 의 값 배정과 호출부 연결은 이름·라이브 관측에 기반하며 완전히 검증되지 않았습니다. 관문별 호출 근거는
    netfunnel.KORAIL_NETFUNNEL_GATES 를 참고하십시오."""

    #: 일반 열차조회. 조회 액션의 기본값 — 달력이 없거나 성수기가 아닌 날 (``TrainScheduleViewModel.java:5225-5234``).
    #: ``KorailTalkApplication.java:382-386`` 이 Property 에 넣는 기본 aid 도 len 5 입니다.
    INQUIRY = "act_8"
    #: 성수기 열차조회. ``RunDateOutItem.isPeakSeason()`` 이 참인 날 (``TrainScheduleViewModel.java:5225-5229``, 판정은
    #: ``bizDdStgCd`` 를 보호된 코드값과 비교 — ``RunDateOutItem.java:516-523``).
    PEAK_SEASON_INQUIRY = "act_8_2"
    #: 상품(특가) 열차조회. ``specialOffer`` 가 있으면(``ACCOMPANY_4`` 제외) 조회 액션이 따로 고른 len 5 문자열이
    #: 됩니다(``TrainScheduleViewModel.java:5213-5215``). 그 문자열이 ``ACTION_PRODUCT_ID`` 라는 것은 **추정(미검증)** 입니다.
    PRODUCT = "act_6"
    #: 예약(회원 ``certification.TicketReservation``·좌석배정 ``reservation.seatAssign.do`` ·비회원
    #: ``nonMember.NonMemTicket``). 호출부는 ``netFunnelTicketReservation``/ ``netFunnelNonMemTicket`` 여섯 곳, 모두 len
    #: 6.
    RESERVE = "act_14"
    #: 결제(``payment.ReservationPayment`` 외). 호출부는 ``PayViewModel.java:6724``, ``FPayViewModel.java:795`` 의
    #: ``executePayment``, len 6.
    PAY = "act_18"
    #: 예약내역 조회(``reservation.ReservationView``). 호출부는 ``MyReservationViewModel.java:2528`` 의
    #: ``reqReservationView``, len 6.
    RESERVED = "act_21"
    #: 테스트. 선언(``NetworkConstants.java:93``)만 있고 호출부는 없습니다.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """대기열 진입·대기·반납 요청 코드를 나타냅니다. 7.0.6 평문 근거: com/netfunnel/api/Command.java:4-21."""

    CHK_ENTER = "5002"
    ALIVE_NOTICE = "5003"
    SET_COMPLETE = "5004"
    GET_TID_CHK_ENTER = "5101"
    INIT = "5105"
    STOP = "5106"


DYNAPATH_HEADER_NAME = "x-dynapath-m-token"
KORAIL_LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
#: DynaPath 대상 경로. DynaPathInterceptor.java:40 은 보호 문자열 여섯 개를 선언합니다. byte[] 길이 다중집합 {38,41,49,49,56,58} 은 아래 경로와
#: 맞지만 평문을 증명하지 않습니다. 헤더 문자열도 보호됨(:34-35). 차단 정수 집합(:41)은 http._DYNAPATH_BLOCK_CODES 에 있습니다. 아래 순서는 라이브러리의
#: 선택입니다.
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
#: DynaPath 비활성화 시 전송 전에 거절하는 경로입니다. 다른 경로도 서버에서 거절될 수 있습니다. 2026-09-24: 토큰 없는 ScheduleView는 MACRO ERROR로
#: 거절됐습니다.
DYNAPATH_REQUIRED_PATHS = frozenset({KORAIL_LOGIN_PATH})
