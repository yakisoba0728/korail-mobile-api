# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""요청 기본값, 공개 열거형·입력 타입과 여러 도메인이 함께 쓰는 예약 코드입니다.

한 모듈만 쓰는 프로토콜 상수는 그 모듈에 둡니다. 보호 리터럴은 코드 배정을 증명하지 않으므로 관측값·기기 표본과 앱
평문 근거를 구분합니다."""

from enum import StrEnum
from typing import Literal, TypeAlias

KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_VERSION = "7.0.8"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
# 기기 기본값은 한 표본 기기의 값입니다. DynaPath 토큰의 dm·os 와 기본 대기열 User-Agent 에 함께 씁니다.
KORAIL_DEFAULT_DEVICE_NAME = "SM-S948N"
# Build.VERSION.RELEASE 이며 SDK 정수(KORAIL_DEFAULT_ANDROID_SDK_INT)와 다릅니다.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "17"
KORAIL_DEFAULT_ANDROID_BUILD_ID = "CP2A.260605.016"
# 앱은 고정 상수 대신 창 크기를 읽습니다. 공통코드 요청에 보냅니다.
KORAIL_DEFAULT_DEVICE_WIDTH = 1440
KORAIL_DEFAULT_DEVICE_HEIGHT = 3120
# 공통코드 요청의 OSVersion 값입니다.
KORAIL_DEFAULT_ANDROID_SDK_INT = 37
# 운영 관측값이며 보호된 헤더 리터럴은 해독하지 않습니다.
KORAIL_API_USER_AGENT = "korailtalk"
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
# evidence: app 7.0.6 NetworkConstants.java:84, KorailTalkApplication.java:387
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0


def build_dalvik_user_agent(*, os_release: str, device_model: str, build_id: str) -> str:
    """대기열 요청에 쓰는 안드로이드 기본 ``User-Agent``(``Dalvik/2.1.0 (...)``) 문자열을 만듭니다.

    기기를 바꿀 때 ``KorailConfig.netfunnel_user_agent``를 DynaPath 기기 값과 맞추는 데 쓰세요. ``device_model``이나
    ``build_id``가 빈 문자열이면 그 부분을 생략하고, ``os_release``가 빈 문자열이면 ``1.0``을 씁니다."""
    # 대기열 SDK 는 User-Agent 를 넣지 않아 HttpURLConnection 이 안드로이드 http.agent 기본값을 붙입니다.
    model = f"; {device_model}" if device_model else ""
    build = f" Build/{build_id}" if build_id else ""
    return f"Dalvik/2.1.0 (Linux; U; Android {os_release or '1.0'}{model}{build})"


KORAIL_USER_AGENT = build_dalvik_user_agent(
    os_release=KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    device_model=KORAIL_DEFAULT_DEVICE_NAME,
    build_id=KORAIL_DEFAULT_ANDROID_BUILD_ID,
)


class KorailReserveOption(StrEnum):
    """간편 예약에서 가용 객실을 고르는 전략입니다. 요청 실패를 재시도하지 않습니다."""

    GENERAL_FIRST = "GENERAL_FIRST"
    GENERAL_ONLY = "GENERAL_ONLY"
    SPECIAL_FIRST = "SPECIAL_FIRST"
    SPECIAL_ONLY = "SPECIAL_ONLY"


class KorailSeatClass(StrEnum):
    """예약할 객실 등급입니다.

    ``GENERAL``(``"1"``)은 일반실, ``SPECIAL``(``"2"``)은 특실입니다."""

    # 앱의 "1"/"2" 배정은 보호돼 미확인입니다.
    # evidence: app 7.0.6 PsrmType.java:19-22, TicketReservationInJrny.java:234

    #: 일반실입니다.
    GENERAL = "1"
    #: 특실입니다.
    SPECIAL = "2"


#: 객실 등급 입력 타입입니다. ``"1"``(일반실), ``"2"``(특실) 또는 ``KorailSeatClass`` 값을 받습니다.
KorailRoomClassCode: TypeAlias = Literal["1", "2"] | KorailSeatClass
#: 로그인 ID 종류입니다. ``"2"``는 회원번호, ``"4"``는 전화번호, ``"5"``는 이메일입니다.
KorailLoginInputFlag: TypeAlias = Literal["2", "4", "5"]


class KorailReservationJobType(StrEnum):
    """예약 종류(일반 예약, 예약대기, 좌석 지정 예약, 병합 예약)를 구분합니다.

    ``reserve``, ``reserve_transfer``, ``reserve_merge``의 ``job_type``에 넣습니다."""

    # 앱의 DEFAULT/WAIT/SEAT/MERGE 등에 대응하나 코드 평문은 보호돼 있습니다.
    # evidence: app 7.0.6 ReservationJobId.java:20-24

    #: 일반 예약입니다. 좌석은 서버가 배정합니다.
    IMMEDIATE = "1101"
    #: 예약대기입니다. 이 종류로 만든 홀드는 ``payable``이 ``False``이며 바로 결제할 수 없습니다.
    STANDBY = "1102"
    #: 좌석 지정 예약입니다. 호차와 좌석을 직접 골라 ``seats``로 넘깁니다.
    SEAT_DESIGNATED = "1103"
    #: 병합 예약입니다. ``reserve``로 첫 홀드를 만들 때와 ``reserve_merge``로 이어서 예약할 때 씁니다.
    MERGE_STANDING = "1202"


# 예약대기를 신청할 수 있는 열차의 wait_reservation_flag 값입니다. 앱의 비교 리터럴은 보호돼 미확인입니다.
# evidence: app 7.0.6 TrainScheduleOutTrainInfo.java:146,1476
KORAIL_STANDBY_WAIT_FLAG = " 9"
# evidence: app 7.0.6 Passengers.java:48
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9
# evidence: app 7.0.6 JourneyDefine.java:22-28 (SequenceNo 값은 보호돼 미확인)
KORAIL_DIRECT_ITINERARY_CODE = "1"
KORAIL_TRANSFER_ITINERARY_CODE = "2"
# evidence: app 7.0.6 JourneyDefine.java:87-90 (평문은 보호돼 미확인)
KORAIL_DIRECT_JOURNEY_TYPE_CODE = "11"
