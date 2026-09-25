# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""보호 리터럴은 코드 배정을 증명하지 않으므로 관측값·기기 표본과 앱 평문 근거를 구분합니다."""

from enum import StrEnum
from typing import Literal, TypeAlias

KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
#: 토큰 dm 은 Build.MODEL(a/b.java:113-116), st 는 별도 평문 "Android"(a/b.java:117). 초기화·생성:
#: DynaPathMobileSDK.java:31-71.
KORAIL_DEFAULT_DEVICE_NAME = "SM-S948N"
#: os 는 Build.VERSION.RELEASE(a/b.java:109-112), SDK 정수와 다릅니다. 필드명 "os": com/kakao/sdk/common/Constants.java:30.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "17"
#: 값: getprop.txt:1032.
KORAIL_DEFAULT_ANDROID_BUILD_ID = "CP2A.260605.016"
#: 실기기 기록: analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:10. 앱은 고정 상수 대신 창 크기를
#: 읽습니다(NetworkService.java:2002,2014). live.build_config_from_env 의 기본 화면 크기도 같은 표본에 맞췄습니다.
KORAIL_DEFAULT_DEVICE_WIDTH = 1440
KORAIL_DEFAULT_DEVICE_HEIGHT = 3120
#: CommonCodeIn.java:91 의 OSVersion 필드. 라우트: NetworkApi.java:315-321.
KORAIL_DEFAULT_ANDROID_SDK_INT = 37


#: API User-Agent는 운영 관측값이며 보호된 헤더 리터럴은 여기서 해독하지 않습니다(NetworkModule.java:405-423).
KORAIL_API_USER_AGENT = "korailtalk"


def build_dalvik_user_agent(*, os_release: str, device_model: str, build_id: str) -> str:
    """안드로이드의 http.agent 기본값을 만듭니다. 대기열 SDK 는 User-Agent 를 넣지 않아(com/netfunnel/api/http/Client.java:252-260)
    HttpURLConnection 이 이 값을 붙입니다."""
    model = f"; {device_model}" if device_model else ""
    build = f" Build/{build_id}" if build_id else ""
    return f"Dalvik/2.1.0 (Linux; U; Android {os_release or '1.0'}{model}{build})"


KORAIL_USER_AGENT = build_dalvik_user_agent(
    os_release=KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    device_model=KORAIL_DEFAULT_DEVICE_NAME,
    build_id=KORAIL_DEFAULT_ANDROID_BUILD_ID,
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
    """예약할 객실 등급을 나타냅니다.

    PsrmType.java:19-22 에 GENERAL/SPECIAL 과 psrmClCd 가 있습니다. "1"/"2" 배정은 보호돼 미확인입니다. 필드명 근거:
    TicketReservationInJrny.java:234."""

    GENERAL = "1"
    SPECIAL = "2"


# 입력에 지원하는 기존 코드만 좁힙니다.
KorailRoomClassCode: TypeAlias = Literal["1", "2"] | KorailSeatClass
KorailLoginInputFlag: TypeAlias = Literal["2", "4", "5"]


class KorailReservationJobType(StrEnum):
    """일반·좌석지정·예약대기·병합 예약 작업을 구분합니다.

    공통 라우트: NetworkApi.java:751-753. ReservationJobId.java:20-24 의 DEFAULT/WAIT/SEAT/MERGE 등에 대응하나 코드 평문은
    보호돼 있습니다."""

    IMMEDIATE = "1101"
    STANDBY = "1102"
    SEAT_DESIGNATED = "1103"
    MERGE_STANDING = "1202"


#: 필드 근거: TrainScheduleOutTrainInfo.java:146,1476. 비교 리터럴은 보호돼 미확인입니다.
KORAIL_STANDBY_WAIT_FLAG = " 9"

#: 7.0.6 의 동일 상한은 미확인입니다.
KORAIL_MAX_DISCOUNT_CARD_SECTIONS = 3

#: ReqDiscount.java:36 / ResDiscount.java:46 에 N_CARD 가 있으나 값은 보호됨. 판정 헬퍼: DiscountHelper.java:818, 호출:
#: TCReservationRequestHelper.java:284.
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"

#: TicketReservationIn.java:43 의 txtMenuId. ReservationMenuId.java:21-22 는 SEAT_ASSIGN 과 N_CARD 를 별개로 선언합니다.
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


#: Passengers.java:48 의 MAX_COUNT=9 는 평문입니다. 합계 함수는 Passengers.java:610-616, 요청 필드는 TicketReservationIn.java:54.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9


# JourneyDefine.java:22-28 의 SequenceNo 값은 보호돼 있습니다. 여정번호 인자는 TrainScheduleOutTrainInfo.java:3683 에서 그대로 DTO 로
# 전달됩니다.
KORAIL_DIRECT_ITINERARY_CODE = "1"
KORAIL_TRANSFER_ITINERARY_CODE = "2"

# 여정종류 필드: TicketReservationInJrny.java:230; enum: JourneyDefine.java:87-90. 환승 여부에 따른 분기:
# TrainScheduleOutTrainInfo.java:3674-3683.
KORAIL_DIRECT_JOURNEY_TYPE_CODE = "11"
KORAIL_TRANSFER_JOURNEY_TYPE_CODE = "14"

# 병합 홀드 응답의 여정 종류는 선행 "21"·후행 "22" 입니다(JourneyDefine.java:89-90, 평문 보호; ·22 라이브 관측). 요청은 여정을 나누지 않습니다 —
# mutation_payloads.build_merge_reservation_form 참고.

#: 필드명: TrainScheduleOutTrainInfo.java:147,1480. 판정 메서드: TrainScheduleOutTrainInfo.java:1500-1552.
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}

#: TicketReservationIn.java:32-54 는 선행·후행 좌석 필드를 한 쌍으로 선언합니다(TicketReservationInSrcarTrailing.java:24-30). 이것은 두
#: 구간 좌석 구성의 근거이며 모든 앱 여정의 하드 상한을 증명하지는 않습니다.
KORAIL_MAX_JOURNEY_LEGS = 2

# NetFunnel 설정·주입은 NetworkConstants.java:80-99와 KorailTalkApplication.java:361-389을 따릅니다. 보호 리터럴은 미확인입니다.
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
#: 요청당 제한시간은 3초입니다(NetworkConstants.java:84; KorailTalkApplication.java:387).
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0
#: 재시도는 첫 시도 외 1회입니다(NetworkConstants.java:83; KorailTalkApplication.java:388). SDK는 실패한 시도 시작부터 제한시간을 채운 뒤
#: 재시도합니다 (Netfunnel.java:352-363; com/netfunnel/api/Property.java:16의 wait_retry_=true).
KORAIL_NETFUNNEL_RETRY = 1


class KorailNetFunnelAction(StrEnum):
    """NetworkConstants.java:88-94 에 액션 상수 일곱 개가 있습니다. 값은 보호돼 있으며 같은 길이의 후보들을 길이만으로 구별할 수 없습니다."""

    #: 조회 액션의 기본값 — 달력이 없거나 성수기가 아닌 날 (``TrainScheduleViewModel.java:5225-5234``).
    #: ``KorailTalkApplication.java:382-386`` 이 Property 에 넣는 기본 aid 도 len 5 입니다.
    INQUIRY = "act_8"
    #: ``RunDateOutItem.isPeakSeason()`` 이 참인 날 (``TrainScheduleViewModel.java:5225-5229``, 판정은 ``bizDdStgCd`` 를
    #: 보호된 코드값과 비교 — ``RunDateOutItem.java:516-523``).
    PEAK_SEASON_INQUIRY = "act_8_2"
    #: ``specialOffer`` 가 있으면(``ACCOMPANY_4`` 제외) 조회 액션이 따로 고른 len 5 문자열이
    #: 됩니다(``TrainScheduleViewModel.java:5213-5215``).
    PRODUCT = "act_6"
    RESERVE = "act_14"
    #: 호출부는 ``PayViewModel.java:6724``, ``FPayViewModel.java:795`` 의 ``executePayment``, len 6.
    PAY = "act_18"
    #: 호출부는 ``MyReservationViewModel.java:2528`` 의 ``reqReservationView``, len 6.
    RESERVED = "act_21"
    #: 선언(``NetworkConstants.java:93``)만 있고 호출부는 없습니다.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """7.0.6 평문 근거: com/netfunnel/api/Command.java:4-21."""

    CHK_ENTER = "5002"
    ALIVE_NOTICE = "5003"
    SET_COMPLETE = "5004"
    GET_TID_CHK_ENTER = "5101"
    INIT = "5105"
    STOP = "5106"


DYNAPATH_HEADER_NAME = "x-dynapath-m-token"
KORAIL_LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
#: DynaPathInterceptor.java:40 은 보호 문자열 여섯 개를 선언합니다. byte[] 길이 다중집합 {38,41,49,49,56,58} 은 아래 경로와 맞지만 평문을 증명하지
#: 않습니다. 헤더 문자열도 보호됨(:34-35).
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
#: DynaPath 비활성화 시 전송 전에 거절하는 경로입니다. 다른 경로도 서버에서 거절될 수 있습니다. 실서버 관측: 토큰 없는 ScheduleView는 MACRO ERROR로 거절됐습니다.
DYNAPATH_REQUIRED_PATHS = frozenset({KORAIL_LOGIN_PATH})
