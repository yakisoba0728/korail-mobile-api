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
# 토큰 dm 은 Build.MODEL(a/b.java:113-116), st 는 별도 평문 "Android"(a/b.java:117). 초기화·생성:
# DynaPathMobileSDK.java:31-71.
#: 기본 기기 모델명입니다. DynaPath 토큰의 기기 모델과 기본 대기열 ``User-Agent``에 씁니다.
KORAIL_DEFAULT_DEVICE_NAME = "SM-S948N"
# os 는 Build.VERSION.RELEASE(a/b.java:109-112), SDK 정수와 다릅니다. 필드명 "os": com/kakao/sdk/common/Constants.java:30.
#: 기본 안드로이드 버전입니다. DynaPath 토큰의 OS 버전과 기본 대기열 ``User-Agent``에 씁니다.
#: SDK 정수(``KORAIL_DEFAULT_ANDROID_SDK_INT``)와 다릅니다.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "17"
# 값: getprop.txt:1032.
#: 기본 대기열 ``User-Agent``에 넣는 안드로이드 빌드 ID입니다.
KORAIL_DEFAULT_ANDROID_BUILD_ID = "CP2A.260605.016"
# 실기기 기록: analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:10. 앱은 고정 상수 대신 창 크기를
# 읽습니다(NetworkService.java:2002,2014). live.build_config_from_env 의 기본 화면 크기도 같은 표본에 맞췄습니다.
#: 기본 화면 너비(픽셀)입니다. 공통코드 요청에 보냅니다.
KORAIL_DEFAULT_DEVICE_WIDTH = 1440
#: 기본 화면 높이(픽셀)입니다. 공통코드 요청에 보냅니다.
KORAIL_DEFAULT_DEVICE_HEIGHT = 3120
# CommonCodeIn.java:91 의 OSVersion 필드. 라우트: NetworkApi.java:315-321.
#: 기본 안드로이드 SDK 정수입니다. 공통코드 요청의 ``OSVersion`` 값으로 보냅니다.
KORAIL_DEFAULT_ANDROID_SDK_INT = 37


# API User-Agent는 운영 관측값이며 보호된 헤더 리터럴은 여기서 해독하지 않습니다(NetworkModule.java:405-423).
#: KORAIL API 요청의 기본 ``User-Agent`` 헤더 값입니다.
KORAIL_API_USER_AGENT = "korailtalk"


def build_dalvik_user_agent(*, os_release: str, device_model: str, build_id: str) -> str:
    """대기열 요청에 쓰는 안드로이드 기본 ``User-Agent``(``Dalvik/2.1.0 (...)``) 문자열을 만듭니다.

    기기를 바꿀 때 ``KorailConfig.netfunnel_user_agent``를 DynaPath 기기 값과 맞추는 데 쓰세요. ``device_model``이나
    ``build_id``가 빈 문자열이면 그 부분을 생략하고, ``os_release``가 빈 문자열이면 ``1.0``을 씁니다."""
    # 안드로이드의 http.agent 기본값입니다. 대기열 SDK 는 User-Agent 를 넣지 않아(com/netfunnel/api/http/Client.java:252-260)
    # HttpURLConnection 이 이 값을 붙입니다.
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
    """예약할 객실 등급입니다.

    ``GENERAL``(``"1"``)은 일반실, ``SPECIAL``(``"2"``)은 특실입니다."""

    # PsrmType.java:19-22 에 GENERAL/SPECIAL 과 psrmClCd 가 있습니다. 앱 쪽 "1"/"2" 배정은 보호돼 미확인입니다. 필드명 근거:
    # TicketReservationInJrny.java:234.

    #: 일반실입니다.
    GENERAL = "1"
    #: 특실입니다.
    SPECIAL = "2"


# 입력에 지원하는 기존 코드만 좁힙니다.
#: 객실 등급 입력 타입입니다. ``"1"``(일반실), ``"2"``(특실) 또는 ``KorailSeatClass`` 값을 받습니다.
KorailRoomClassCode: TypeAlias = Literal["1", "2"] | KorailSeatClass
#: 로그인 ID 종류입니다. ``"2"``는 회원번호, ``"4"``는 전화번호, ``"5"``는 이메일입니다.
KorailLoginInputFlag: TypeAlias = Literal["2", "4", "5"]


class KorailReservationJobType(StrEnum):
    """예약 종류(일반 예약, 예약대기, 좌석 지정 예약, 병합 예약)를 구분합니다.

    ``reserve``, ``reserve_transfer``, ``reserve_merge``의 ``job_type``에 넣습니다."""

    # 공통 라우트: NetworkApi.java:751-753. ReservationJobId.java:20-24 의 DEFAULT/WAIT/SEAT/MERGE 등에 대응하나 코드 평문은
    # 보호돼 있습니다.

    #: 일반 예약입니다. 좌석은 서버가 배정합니다.
    IMMEDIATE = "1101"
    #: 예약대기입니다. 이 종류로 만든 홀드는 ``payable``이 ``False``이며 바로 결제할 수 없습니다.
    STANDBY = "1102"
    #: 좌석 지정 예약입니다. 호차와 좌석을 직접 골라 ``seats``로 넘깁니다.
    SEAT_DESIGNATED = "1103"
    #: 병합 예약입니다. ``reserve``로 첫 홀드를 만들 때와 ``reserve_merge``로 이어서 예약할 때 씁니다.
    MERGE_STANDING = "1202"


# 필드 근거: TrainScheduleOutTrainInfo.java:146,1476. 비교 리터럴은 보호돼 미확인입니다.
#: 예약대기를 신청할 수 있는 열차의 ``wait_reservation_flag`` 값입니다. 앱이 비교하는 값은 앱 내부 값이 공개돼 있지 않아
#: 확인하지 못했습니다.
KORAIL_STANDBY_WAIT_FLAG = " 9"

# 7.0.6 의 동일 상한은 미확인입니다.
#: N카드 구매 한 번에 넣을 수 있는 구간 수의 상한입니다. 앱의 상한과 같은지는 확인하지 못했습니다.
KORAIL_MAX_DISCOUNT_CARD_SECTIONS = 3

# ReqDiscount.java:36 / ResDiscount.java:46 에 N_CARD 가 있으나 값은 보호됨. 판정 헬퍼: DiscountHelper.java:818, 호출:
# TCReservationRequestHelper.java:284.
#: N카드로 예약할 때 보내는 할인 종류 코드입니다. 앱의 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"

# TicketReservationIn.java:43 의 txtMenuId. ReservationMenuId.java:21-22 는 SEAT_ASSIGN 과 N_CARD 를 별개로 선언합니다.
#: N카드로 예약할 때 보내는 메뉴 ID(``txtMenuId``)입니다.
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


# Passengers.java:48 의 MAX_COUNT=9 는 평문입니다. 합계 함수는 Passengers.java:610-616, 요청 필드는 TicketReservationIn.java:54.
#: 예약 한 건에 넣을 수 있는 승객 수의 상한입니다.
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

# 필드명: TrainScheduleOutTrainInfo.java:147,1480. 판정 메서드: TrainScheduleOutTrainInfo.java:1500-1552.
#: 객실 등급 코드별로 병합 예약을 할 수 있는 ``merge_seat_application_flag`` 값입니다. 일반실(``"1"``)은 ``"A"``·``"G"``,
#: 특실(``"2"``)은 ``"A"``·``"S"``입니다.
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}

# TicketReservationIn.java:32-54 는 선행·후행 좌석 필드를 한 쌍으로 선언합니다(TicketReservationInSrcarTrailing.java:24-30). 이것은
# 두 구간 좌석 구성의 근거이며 모든 앱 여정의 하드 상한을 증명하지는 않습니다.
#: 예약 한 건에 넣을 수 있는 구간 수의 상한입니다.
KORAIL_MAX_JOURNEY_LEGS = 2

# NetFunnel 설정·주입은 NetworkConstants.java:80-99와 KorailTalkApplication.java:361-389을 따릅니다. 보호 리터럴은 미확인입니다.
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
# 요청당 제한시간은 3초입니다(NetworkConstants.java:84; KorailTalkApplication.java:387).
#: 대기열 요청 하나의 기본 제한 시간(초)입니다.
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0
# 재시도는 첫 시도 외 1회입니다(NetworkConstants.java:83; KorailTalkApplication.java:388). SDK는 실패한 시도 시작부터 제한시간을
# 채운 뒤 재시도합니다 (Netfunnel.java:352-363; com/netfunnel/api/Property.java:16의 wait_retry_=true).
#: 관문을 통과하는 동안 실패한 대기열 요청을 다시 보내는 횟수입니다. 다시 보내기 전에는 실패한 요청의 제한 시간이 다 찰
#: 때까지 기다립니다.
KORAIL_NETFUNNEL_RETRY = 1


class KorailNetFunnelAction(StrEnum):
    """대기열 관문별로 대기열 서버에 보내는 식별값(``aid``)입니다.

    앱이 쓰는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 다른 값이 필요하면 ``KorailConfig.netfunnel_actions``로
    관문별 값을 바꾸세요."""

    # NetworkConstants.java:88-94 에 액션 상수 일곱 개가 있습니다. 값은 보호돼 있으며 같은 길이의 후보들을 길이만으로 구별할 수
    # 없습니다. 기본값은 길이와 호출부 문맥으로 고른 미확인 값입니다.

    # 조회 액션의 기본값 — 달력이 없거나 성수기가 아닌 날 (TrainScheduleViewModel.java:5225-5234).
    # KorailTalkApplication.java:382-386 이 Property 에 넣는 기본 aid 도 len 5 입니다.
    #: 열차 조회(``inquiry`` 관문)의 식별값입니다.
    INQUIRY = "act_8"
    # RunDateOutItem.isPeakSeason() 이 참인 날 (TrainScheduleViewModel.java:5225-5229, 판정은 bizDdStgCd 를 보호된 코드값과
    # 비교 — RunDateOutItem.java:516-523).
    #: 성수기 날짜의 열차 조회(``peak_season_inquiry`` 관문)의 식별값입니다.
    PEAK_SEASON_INQUIRY = "act_8_2"
    # specialOffer 가 있으면(ACCOMPANY_4 제외) 조회 액션이 따로 고른 len 5 문자열이 됩니다(TrainScheduleViewModel.java:5213-5215).
    #: ``use_special_schedule=True``인 열차 조회(``product_inquiry`` 관문)의 식별값입니다.
    PRODUCT = "act_6"
    #: 예약(``reserve`` 관문)의 식별값입니다.
    RESERVE = "act_14"
    # 호출부는 PayViewModel.java:6724, FPayViewModel.java:795 의 executePayment, len 6.
    #: 결제(``pay`` 관문)의 식별값입니다.
    PAY = "act_18"
    # 호출부는 MyReservationViewModel.java:2528 의 reqReservationView, len 6.
    #: 예약 내역 조회(``reservation_view`` 관문)의 식별값입니다.
    RESERVED = "act_21"
    # 선언(NetworkConstants.java:93)만 있고 호출부는 없습니다.
    #: 앱에 선언만 있는 값입니다. 라이브러리는 이 값을 쓰지 않습니다.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """대기열 서버에 보내는 명령 코드(``opcode``)입니다."""

    # 7.0.6 평문 근거: com/netfunnel/api/Command.java:4-21.

    #: 입장 키로 입장 가능 여부를 다시 확인합니다.
    CHK_ENTER = "5002"
    #: 라이브러리는 이 값을 쓰지 않습니다.
    ALIVE_NOTICE = "5003"
    #: 작업을 마치고 입장 키를 반납합니다.
    SET_COMPLETE = "5004"
    #: 입장 키를 받고 입장 가능 여부를 확인합니다.
    GET_TID_CHK_ENTER = "5101"
    #: 라이브러리는 이 값을 쓰지 않습니다.
    INIT = "5105"
    #: 라이브러리는 이 값을 쓰지 않습니다.
    STOP = "5106"


DYNAPATH_HEADER_NAME = "x-dynapath-m-token"
KORAIL_LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
# DynaPathInterceptor.java:40 은 보호 문자열 여섯 개를 선언합니다. byte[] 길이 다중집합 {38,41,49,49,56,58} 은 아래 경로와 맞지만
# 평문을 증명하지 않습니다. 헤더 문자열도 보호됨(:34-35).
#: DynaPath 토큰을 붙이는 API 경로입니다. 앱의 경로 목록은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
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
# 실서버 관측: 토큰 없는 ScheduleView는 MACRO ERROR로 거절됐습니다.
#: DynaPath를 끈 설정에서 요청 전에 거절하는 경로(로그인)입니다. 다른 경로도 토큰이 없으면 서버가 거절할 수 있습니다.
DYNAPATH_REQUIRED_PATHS = frozenset({KORAIL_LOGIN_PATH})
