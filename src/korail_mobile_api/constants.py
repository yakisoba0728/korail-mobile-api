# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""앱 디컴파일에서 읽은 상수 — 엔드포인트, 기기 기본값, 코드값.

이 모듈의 근거는 **7.0.6** 기준입니다.
7.0.6 에서 대응물을 찾지 못한 값은 그 자리에 **미출처**라고 적혀 있습니다.

각 값 옆에 근거가 ``파일:줄`` 로 붙어 있습니다 — 대부분 APK 정적 분석입니다.
예외 셋: ``KORAIL_DEFAULT_DEVICE_WIDTH``/``KORAIL_DEFAULT_DEVICE_HEIGHT``/
``KORAIL_DEFAULT_ANDROID_SDK_INT`` 는 APK 정적 분석으로 값 자체를 얻을 수
없습니다(요청 시점에 ``ContextExKt.getWindowSize(...)``/``Build.VERSION.SDK_INT``
를 실기기에서 읽습니다 — 아래 각 상수의 주석 참고). 이 셋은 대신 이 저장소에
있는 유일한 7.0.6 실기기 샘플(``analysis/device-pull/``)에 맞췄습니다 — 그것도
근거이지 추측이 아니지만, "APK 근거" 는 아닙니다.
닫힌 코드 집합은 :class:`StrEnum` 으로 둡니다.

7.0.6 인용 규칙
---------------
7.0.6 은 AlienGuard/AppSuit 문자열
난독화를 쓰므로 코틀린 **속성/필드/enum 이름과 ``@SerialName`` 은 읽히지만
리터럴 문자열 값은 읽히지 않습니다**(``AlienGuard1789016769018.method_name_*``
런타임 복호화). 그래서 값 근거를 다음 세 등급으로 나눠 적었습니다.

* **읽힘** — 평문 리터럴이 디컴파일에 그대로 있음(정수 상수,
  ``com/netfunnel/**`` 와 DynaPath SDK 내부처럼 난독화가 안 걸린 패키지,
  ``@SerialName``).
* **길이 일치** — 리터럴은 보호됐지만 ``method_name_*`` 의 ``byte[]`` 인자
  **길이가 평문 길이와 같다**. 이 대응은 ``DynaPathInterceptor.java:40`` 에서
  검증했습니다 — 그 ``setOf`` 의 여섯 ``byte[]`` 길이가
  ``{38,41,49,49,56,58}`` 로, :data:`DYNAPATH_ALLOWLIST_PATHS` 여섯 경로의
  평문 길이 다중집합과 정확히 같습니다. 길이는 값을 **제약**할 뿐 증명하지
  않으므로(같은 길이 후보가 여럿이면 못 가림), 그 경우 필드 **이름**이
  나머지를 맡습니다.
* **미출처** — 7.0.6 에 대응 근거가 없음. 실서버로 확인된 값이면 그렇게
  적습니다. 지어낸 인용을 붙이지 않습니다.
"""

from enum import StrEnum


KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
#: DynaPath ``dm`` 필드 = ``Build.MODEL``
#: (``analysis/jadx/sources/a/b.java:113-116``). **읽힘.**
#: 특정 기종 대신 일반 문자열로 둡니다. 실제 기기로 고정하려면
#: :func:`~korail_mobile_api.live.build_config_from_env` 를 씁니다.
#: ``st`` 필드는 별도 리터럴 ``"Android"``(``a/b.java:117``). **읽힘** —
#: DynaPath SDK 내부(``a``/``b`` 패키지)에는 AlienGuard 가 걸려 있지 않아
#: ``linkedHashMap.put("st", new String[]{"Android"})`` 가 그대로 보입니다.
#: 이 SDK 는 ``kr.scripters.dynapath.sdk.android.DynaPathMobileSDK``
#: (``DynaPathMobileSDK.java:31-52``, ``:64``)로 들어오고 토큰 조립은
#: ``a/b.java:75-227`` 의 ``a()`` 입니다.
KORAIL_DEFAULT_DEVICE_NAME = "Android"
#: DynaPath ``os`` 필드 = ``Build.VERSION.RELEASE``(``a/b.java:109-112``;
#: 키는 ``com.kakao.sdk.common.Constants.OS``, 그 값은 ``Constants.java:30``
#: 의 ``"os"``). **읽힘.**
#: ``Build.VERSION.SDK_INT`` 와 다릅니다 — SDK 정수는 아래
#: :data:`KORAIL_DEFAULT_ANDROID_SDK_INT`.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "15"
#: 실기기 근거:
#: ``analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:10``
#: (``wm_size Physical size: 1440x3120``). APK 정적 분석은 이 값을 만들지
#: 않습니다 — ``NetworkService.java:2002,2014`` 가 요청 시점에
#: ``ContextExKt.getWindowSize(...)`` 를 실기기에서 읽습니다. 이 저장소에
#: 있는 유일한 7.0.6 기기 샘플에 맞춘 값이며,
#: :func:`~korail_mobile_api.live.build_config_from_env` 의 같은 이름
#: 환경변수 폴백과 일부러 같은 값으로 둡니다 — 둘 다 "더 나은 값이 없어서"
#: 존재하는 기본값이고, 둘이 달라야 할 근거가 없습니다.
KORAIL_DEFAULT_DEVICE_WIDTH = 1440
KORAIL_DEFAULT_DEVICE_HEIGHT = 3120
#: ``Build.VERSION.SDK_INT``. ``common.code.do`` 의 ``OSVersion`` 필드는
#: 7.0.6 에서 ``CommonCodeIn.java:91`` 의 ``@SerialName("OSVersion")``
#: (코틀린 속성은 ``osVersion``, ``:34``)로 확인됩니다 — ``@SerialName`` 은
#: 난독화가 안 걸려 **읽힘**. 라우트는 ``NetworkApi.java:315-321``
#: (``POST /classes/com.korail.mobile.common.code.do``, ``postCommonCode`` 와
#: ``postCommonCodeMulti`` 두 선언). 이것은 **필드명 근거일 뿐**입니다 — 37 자체의 근거는
#: 실기기 샘플입니다: ``summary.tsv:5``(``sdk 37``),
#: ``getprop.txt:1055``(``[ro.build.version.sdk]: [37]``) 로 교차
#: 확인됩니다. 이 기기의 ``release`` 도 17 입니다(``summary.tsv:4``) —
#: 같은 기기 샘플이 안드로이드 릴리스와 SDK 정수를 동시에 보고합니다.
KORAIL_DEFAULT_ANDROID_SDK_INT = 37


def build_dalvik_user_agent(*, os_release: str, device_model: str) -> str:
    """Dalvik User-Agent 를 앱이 보내는 모양으로 만듭니다.

    ``com.korail.talk`` 은 UA 를 하드코딩하지 않습니다 —
    ``com/korail/talk/network/`` 어디에도 ``User-Agent`` 를 넣는
    ``addHeader``/``.header(...)`` 호출이 없습니다.

    7.0.6 은 **Retrofit 2 + OkHttp** 스택입니다
    (``network/di/NetworkModule.java:55-64`` 의 ``okhttp3.OkHttpClient`` /
    ``retrofit2.Retrofit`` import, ``:96`` ``provideApiService(Retrofit)``).
    OkHttp 의 기본 UA 는 ``okhttp3/internal/Util.java:87`` 의
    ``userAgent = "okhttp/4.12.0"`` 이므로, 7.0.6 실제 앱이 보내는 UA 는
    Dalvik 문자열이 아니라 ``okhttp/4.12.0`` 일 가능성이 높습니다.

    그런데도 이 함수가 만드는 Dalvik 모양을 그대로 두는 이유는 **실서버
    관측**입니다 — Python 패키지 이름이 든 UA 로는 로그인이 거절되고 이
    문자열로는 통과합니다. 즉 이 값은 "앱을 그대로 재현한 값" 이
    아니라 "서버가 받아 주는 것을 확인한 값" 이고, APK 근거로는 **미출처**
    입니다. 서버가 ``okhttp/4.12.0`` 도
    받아 주는지는 확인하지 않았습니다(라이브 호출 필요).

    끝의 ``Build/<id>`` 는 뺐습니다 — 기기 모델과 맞지 않는 빌드 id 를
    지어내면 검증 못 할 주장이 됩니다.
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

    7.0.6 대응은 ``PsrmType``(``common/define/PsrmType.java:16-20``) —
    ``GENERAL``(``:19``)/``SPECIAL``(``:20``) 둘뿐이고 각 항목의
    ``psrmClCd``(``:22``) 는 **길이 1** 입니다(``byte[]`` 길이 = 1, 이름
    길이 7/7 과 함께 일치). ``"1"``/``"2"`` 배정 자체는 AlienGuard 로 가려져
    재확인하지 못했습니다. 와이어 필드명은
    ``TicketReservationInJrny.java:234`` 의 ``@SerialName("txtPsrmClCd")``
    (속성 ``txtPsrmClCd``, ``:44``)로 **읽힘**.

    ``ALL`` 은 검색 와일드카드이지 객실이 아니어서 여기에 없습니다. 7.0.6
    ``PsrmType`` 에도 ``ALL`` 항목이 없으며 "전체" 를 뜻하는 ``psrmClCd``
    리터럴도 찾지 못했습니다 — **미출처**.
    """

    GENERAL = "1"
    SPECIAL = "2"


class KorailReservationJobType(StrEnum):
    """``txtJobId`` — 예매 동작 종류.

    넷 다 같은 경로로 갑니다 — 7.0.6 선언은
    ``NetworkApi.java:751-753``(``@FormUrlEncoded`` +
    ``@POST("/classes/com.korail.mobile.certification.TicketReservation")``
    + ``postTicketReservation``). **읽힘.**

    네 값은 모두 ``TicketReservationIn.txtJobId``
    (``TicketReservationIn.java:41``)로 실립니다.

    7.0.6 에서 이 네 코드의 정본은 ``ReservationJobId``
    (``common/define/ReservationJobId.java:16-24``)이고, 각 항목은
    ``jobId``(``:19``)를 들고 있습니다. 다섯 항목 전부 ``jobId`` 쪽
    ``byte[]`` 길이가 **4** 라서 네 자리 코드라는 것까지는 **길이 일치**로
    확인되지만, ``"1101"``/``"1102"``/``"1103"``/``"1202"`` 배정 자체는
    AlienGuard 로 가려져 재확인하지 못했습니다.

    * :attr:`IMMEDIATE`(``"1101"``) — 기본. 7.0.6:
      ``ReservationJobId.DEFAULT``(``ReservationJobId.java:20``). 화면 쪽
      ``TicketReservationType``(``ui/screen/train/TicketReservationType.java``)
      의 ``DEFAULT``/``STAND``/``FREE`` 세 항목이 모두
      ``ReservationJobId.DEFAULT.getJobId()`` 를 재사용합니다(``:38-40``) —
      즉 즉시예매·입석·자유석이 한 job id 를 씁니다.
    * :attr:`STANDBY`(``"1102"``) — 예약대기. 7.0.6:
      ``ReservationJobId.WAIT``(``ReservationJobId.java:21``) 와
      ``TicketReservationType.WAIT``(``TicketReservationType.java:41``,
      ``ReservationJobId.WAIT.getJobId()`` 를 넘김).
      순서(DEFAULT/WAIT/SEAT/MERGE, +새 5번째 ``GROUP_TICKET_SELECT``,
      ``:24``)는 이 enum 의 네 값과 1:1로 대응합니다.
    * :attr:`SEAT_DESIGNATED`(``"1103"``) — 좌석 선택 결과. 7.0.6:
      ``ReservationJobId.SEAT``(``ReservationJobId.java:22``).
      ``TicketReservationType`` 에는 대응 항목이 **없습니다**(다섯 항목이
      DEFAULT/STAND/FREE/WAIT/MERGE) — 좌석지정은 화면 타입이 아니라 job id
      로만 구분되는 것으로 보입니다.
    * :attr:`MERGE_STANDING`(``"1202"``) — 입석+좌석. 7.0.6 대응은
      ``ReservationJobId.MERGE``(``ReservationJobId.java:23``)와
      ``TicketReservationType.MERGE``(``ui/screen/train/TicketReservationType.java:42``).

      병합 화면으로 보낼지는 홀드 응답이 아니라 **자기가 보낸 요청의
      ``txtJobId``** 로 정합니다(``TrainScheduleViewModel.java:6773-6779``):
      ``txtJobId = ticketReservationIn2.getTxtJobId()``(``:6773``) 를
      ``TicketReservationType.MERGE.getJobId()``(``:6774``)와 견주어
      (``:6776``) 참이면 ``ReservationMergeRoute``(``:6777``), 아니면
      ``TicketReservationType.WAIT.getJobId()`` 와 견주어
      ``ReservationWaitRoute``(``:6778-6779``), 그 밖이면
      ``PayRoute``(``:6781``)로 갑니다. 응답 쪽 ``h_jrny_tp_cd`` 필드는
      따로 있고(``ReservationOutJrnyInfo.java:47``, ``@SerialName`` 은
      ``:365``), 이 분기는 그 필드를 읽지 않습니다.
    """

    IMMEDIATE = "1101"
    STANDBY = "1102"
    SEAT_DESIGNATED = "1103"
    MERGE_STANDING = "1202"


#: 예약대기 대상 ``h_wait_rsv_flg`` 값 — " 9"(공백+9).
#:
#: **필드는 출처가 있고 값은 없습니다.** 7.0.6 에서 이 응답 필드는
#: ``TrainScheduleOutTrainInfo`` 의 ``hWaitRsvFlg``(``:146``)이고 와이어 키는
#: ``@SerialName("h_wait_rsv_flg")``(``:1476``) 입니다 — **읽힘**.
#: 그런데 이 게터를 참조하는 곳은 7.0.6 전체에서 DTO 자신뿐입니다
#: (smali 전수 검색 결과 ``smali_classes6/.../TrainScheduleOutTrainInfo.smali``
#: 하나) — 소비부는 전부 AppSuitLinker 리플렉션 디스패처를 거치므로
#: " 9" 와 비교하는 분기를 정적으로 되찾을 수 없습니다.
#: 따라서 리터럴 " 9" 는 **미출처** — 실서버 동작으로는 맞게 쓰이고
#: 있습니다. 앞의 공백은 실수가 아니라 원문 그대로입니다.
KORAIL_STANDBY_WAIT_FLAG = " 9"

#: 예약대기 확인 메시지 코드.
#:
#: 7.0.6 근거: ``analysis/apktool/assets/error_json.json:3181`` 의
#: ``"IRR000014": "예약대기 가능합니다."`` — **읽힘**(자산 JSON 은 난독화
#: 대상이 아님). 즉 이 코드는 오류가 아니라 "예약대기가 가능하다" 는
#: 안내이고, 실패가 아님(``strResult`` = ``SUCC``)이라는 서술은 이 사전이
#: 뒷받침합니다.
#:
#: 다만 "이 코드에서만 예약대기 화면으로 넘어간다" 는 **분기** 주장은
#: 7.0.6 에서 확인하지 못했습니다 — 대응 화면(``ui/screen/train/ReservationWaitViewModel.java``)에서 비교되는
#: 코드 문자열은 AlienGuard 로 가려져 있습니다. 분기는 **미출처**.
KORAIL_STANDBY_HOLD_MESSAGE_CODE = "IRR000014"

#: 할인카드(N카드) 최대 구간 수.
#:
#: **미출처.** 7.0.6 의 N카드 화면은 Compose 로 하나씩
#: (``ui/screen/product/CheckUsageNCardSectionScreenKt.java``,
#: ``ui/screen/myticket/reservation/NCardReservationViewModel.java``)이고,
#: 3 을 상한으로 두는 상수·배열·비교를 7.0.6 어디에서도 찾지 못했습니다.
#: 실동작과 어긋난 관측이 없어 값을 둡니다.
KORAIL_MAX_DISCOUNT_CARD_SECTIONS = 3

#: N카드 할인종류 코드.
#:
#: 7.0.6 에서 이 코드는 ``discKndCd`` 를 들고 있는 두 enum 의 ``N_CARD``
#: 항목입니다 — 요청 쪽 ``ReqDiscount.N_CARD``(``ReqDiscount.java:36``,
#: 필드 ``discKndCd`` 는 ``:20``), 응답 쪽 ``ResDiscount.N_CARD``
#: (``ResDiscount.java:46``, 필드는 ``:25``). 두 항목 모두 ``discKndCd``
#: 쪽 ``byte[]`` 길이가 **3** 이라 세 자리 코드임은 **길이 일치**로
#: 확인됩니다. 다만 두 enum 의 항목 전부가 길이 3 이므로 길이만으로는
#: ``"153"`` 을 가려낼 수 없습니다 — 그 몫은 항목 이름 ``N_CARD`` 가
#: 합니다. 리터럴 자체는 AlienGuard 로 가려져 **재확인 못 함**.
#:
#: 와이어 필드는 ``TicketReservationInPassengerInfo.txtDiscKndCd``
#: (``TicketReservationInPassengerInfo.java:33``).
#:
#: 판정 헬퍼는 ``common/helper/DiscountHelper.java:818`` 의
#: ``public final boolean isNCard(String dcntKndCd)`` 가 넘겨받은 할인코드를
#: ``ReqDiscount.N_CARD`` 와 비교합니다. 호출 예는
#: ``common/helper/TCReservationRequestHelper.java:284`` 입니다 --
#: ``STLjgf()``(``:221``) 안에서 ``DiscountHelper.INSTANCE``(``:274``)를 받아
#: 할인코드 문자열 하나를 넘겨 부릅니다(``!discountHelper.isNCard(...)``).
#: ``MyTicketListOutReservation.java:809-813`` 의 같은 이름 **무인자**
#: 메서드 ``isNCard()`` 와 화면 라우트의 동명 불리언 인자
#: (``ui/navigation/PassengerTypeChangeRoute.java:39``)는 이 헬퍼와 별개입니다.
#:
#: 비교 대상 ``ReqDiscount.N_CARD`` 의 실제 코드 리터럴은 AppSuit 로 보호돼
#: 있어, 그것이 여기 적힌 ``"153"`` 과 같은지는 여전히 확인하지 못했습니다.
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"

#: N카드 예약 ``txtMenuId``. 와이어 필드는
#: ``TicketReservationIn.txtMenuId``(``TicketReservationIn.java:43``).
#:
#: 7.0.6 의 정본은 ``ReservationMenuId``
#: (``common/define/ReservationMenuId.java:14-24``, 게터 ``:65``) — 일곱
#: 항목(``DEFAULT``/``DISCOUNT``/``FAMILY``/``SEAT_ASSIGN``/``N_CARD``/
#: ``PASS_SEAT_ASSIGN``/``GROUP_TICKET``)이고 **전부 ``menuId`` 길이 2**
#: (**길이 일치**). ``"A2"`` 라는 배정은 AlienGuard 로 가려져 재확인하지
#: 못했습니다.
#:
#: **주의 — 이름이 갈라져 있습니다.** 이 값은 좌석지정의 ``A2`` 와 같은
#: 값을 N카드 예약에 씁니다. 그런데 7.0.6 은
#: ``ReservationMenuId.SEAT_ASSIGN``(``:21``)과
#: ``ReservationMenuId.N_CARD``(``:22``)를 **별개 항목**으로 둡니다. 둘의
#: ``menuId`` 가 같은 값인지 다른 값인지는 리터럴이 보호돼 확인할 수
#: 없습니다. 두 메뉴 id 를 하나로 합쳐 쓰는 것이 맞는지는 **열린 문제**입니다.
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


#: 예약 최대 승객 수.
#:
#: 7.0.6 근거: ``common/define/Passengers.java:48`` 의
#: ``public static final int MAX_COUNT = 9;`` — **읽힘**(정수 상수는
#: AlienGuard 대상이 아님). 같은 클래스 ``:49`` 의 ``UNIT = 1`` 이 증감
#: 단위이고, 인원은 ``dataMap``(``:50``, ``Map<PassengerType,Integer>``)에
#: 유형별로 담깁니다 — 즉 9 는 **유형별 상한이 아니라 합계 상한**으로
#: 봅니다. 다만 "합계" 로 더하는 검증 함수 본문은
#: ``Passengers.Companion.validation``(``:99-107`` 계열)이 AppSuitLinker
#: 로 흩어져 있어 9 와 견주는 지점 자체는 정적으로 못 짚었습니다.
#: 와이어에는 ``TicketReservationIn.txtTotPsgCnt``
#: (``TicketReservationIn.java:54``)로 실립니다.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9


# ---------------------------------------------------------------------------
# 환승 — 여정 하나, 구간 둘.
#
# 7.0.6 정본: JourneyDefine.SequenceNo(common/define/JourneyDefine.java:22-26).
#   DIRECT_SQ_NO   :25
#   TRANSFER_SQ_NO :26
#
# 각 항목은 (displayName, code) 를 들고 있고(:27-28), byte[] 길이가
# 길이 일치로 아래 값을 뒷받침합니다:
#   DIRECT_SQ_NO   이름 12, displayName 6, code 1  → "직통"(UTF-8 6바이트), "1"
#   TRANSFER_SQ_NO 이름 14, displayName 6, code 1  → "환승"(UTF-8 6바이트), "2"
# 리터럴 자체는 AlienGuard 로 가려져 있지만, 한글 두 글자(6바이트)와 한 자리
# 코드(1바이트)라는 모양까지는 확인됩니다.
#
# 이 코드는 검색 job id, txtJrnyCnt, txtJrnySqno 씨앗으로 세 가지 일을 합니다.
#
# 세 자리 0 채움("001"/"002")은 미출처입니다. 자리를 받는 필드는 TicketReservationInJrny.txtJrnySqno
# (TicketReservationInJrny.java:42, @SerialName 은 :226)로 확인되지만, 값을
# 조립하는 쪽은 AppSuitLinker 리플렉션 뒤에 있어 padStart(3,'0') 에 해당하는
# 코드를 7.0.6 에서 찾지 못했습니다(읽히는 padStart 호출은 모두 시각 2자리나
# ogtkSaleSqno 5자리용입니다 — 예: StationTicketRefundResultScreenKt.java:788).
# 세 자리 전송 자체는 실서버 동작으로 확인됐습니다.
KORAIL_DIRECT_ITINERARY_CODE = "1"
KORAIL_TRANSFER_ITINERARY_CODE = "2"

# txtJrnyTpCd 와이어 필드: TicketReservationInJrny.txtJrnyTpCd
# (TicketReservationInJrny.java:43, @SerialName("txtJrnyTpCd") 은 :230, 그리고
# 직렬화 생성자 :69 에도 같은 이름이 붙어 있습니다) — 읽힘.
#
# 7.0.6 정본: JourneyDefine.TypeCode(common/define/JourneyDefine.java:79-90),
# 조회는 findBy(String code)(:101).
#   DIRECT   :87  이름 6,  displayName 6,  code 2  → "직통", "11"
#   TRANSFER :88  이름 8,  displayName 6,  code 2  → "환승", "14"
# 길이 일치(한글 두 글자 6바이트 + 두 자리 코드 2바이트)까지는 확인됩니다.
# "11"/"14" 배정 자체는 리터럴이 보호돼 재확인 못 함.
#
# "환승은 두 구간 모두 14" 는 미출처입니다 — jrnyList
# (TicketReservationIn.java:34)를 두 항목으로 채우는 코드는 AppSuitLinker
# 뒤에 있어 배열 길이를 보고 값을 정하는 분기를 되찾지 못했습니다. 두 구간
# 모두 이 값으로 보내면 서버가 받아들인다는 것은 실서버로 확인됐습니다.
KORAIL_DIRECT_JOURNEY_TYPE_CODE = "11"
KORAIL_TRANSFER_JOURNEY_TYPE_CODE = "14"

# ---------------------------------------------------------------------------
# 병합예약 — 열차 하나를 중간역에서 나눠 앞뒤를 다르게 앉힘.
#
# 7.0.6 정본: JourneyDefine.TypeCode(common/define/JourneyDefine.java:79-90)
# 의 나머지 두 항목 —
#   STANDING_SEAT_1 :89  이름 15, displayName 13, code 2
#   STANDING_SEAT_2 :90  이름 15, displayName 13, code 2
# 길이 일치: "병합 선행"/"병합 후행" 은 UTF-8 로 3+3+1+3+3 = 13바이트이고,
# "21"/"22" 는 2바이트입니다. 리터럴 "21"/"22" 자체는 AlienGuard 로 가려져
# 재확인 못 함 — 다만 아래 실서버 확인이 그 자리를 메웁니다.
#
# 7.0.6 정적분석(ReservationMergeViewModel.smali:7223-7821,
# ticketReservation())으로 보면, 최종 재제출은 원래 입석 홀드 요청을
# TicketReservationIn.copy() 로 복제해 txtStndFlg 와 중간역 3개 필드만 바꾸는 것으로 보입니다 — 즉
# jrnyList·txtJrnyCnt·txtJobId 는 원본(입석 홀드) 값 그대로 유지되고,
# 클라이언트가 두 여정을 직접 조립하지 않을 가능성이 있습니다(jadx 디컴파일
# 실패로 스몰리 재구성에 의존한 결과라 완전히 확정하지는 못했습니다). 다만
# 아래 "21"/"22" 코드 자체와 이 값으로 두 여정을 구성해 보내는 방식은
# 2026-09-21 실서버로 직접 확인됐습니다 — 홀드 응답의 h_jrny_tp_cd 가
# 정확히 "21"/"22" 로 갈려 돌아왔고 입석/좌석 두 구간이 문서대로 분리됐습니다.
# 그러니 이 라이브러리의 두 여정 조립 방식이 현재 APK 의 클라이언트 구성과
# 토씨까지 같다고 단정하진 않되, 서버가 실제로 받아들이고 기대한 대로
# 응답한다는 것은 지어낸 게 아니라 확인된 사실입니다.
KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE = "21"
KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE = "22"

#: 병합 대상 판정 ``h_yms_apl_flg`` — 객실별.
#:
#: **필드는 출처가 있고 표는 없습니다.** 7.0.6 에서 이 응답 필드는
#: ``TrainScheduleOutTrainInfo`` 의 ``hYmsAplFlg``(``:147``), 와이어 키는
#: ``@SerialName("h_yms_apl_flg")``(``:1480``) — **읽힘**.
#: 그러나 ``hWaitRsvFlg`` 와 똑같이, 이 게터를 참조하는 곳은 smali 전수
#: 검색에서 DTO 자신뿐입니다 — 소비부가 전부 AppSuitLinker 리플렉션을
#: 거치므로 어느 객실 등급에 어느 플래그 집합이 붙는지를 정적으로 되찾을
#: 수 없습니다 — 이 표는 **미출처**입니다.
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}

#: 예약 최대 구간 수 = 2.
#:
#: 7.0.6 근거는 요청 DTO 의 **모양 자체**입니다 — ``TicketReservationIn``
#: (``TicketReservationIn.java:32-54``)이 "선행/후행" 을 리스트 하나가
#: 아니라 **한 쌍의 별도 필드**로 들고 있고, 셋째 자리가 없습니다:
#:
#: * ``srcarList: List<TicketReservationInSrcar>``(``:36``) +
#:   ``trailingSrcarList: List<TicketReservationInSrcarTrailing>``(``:37``)
#: * ``txtSrcarCnt``(``:52``) + ``trailingTxtSrcarCnt``(``:39``)
#: * ``txtSeatAttCd4``(``:50``) + ``trailingTxtSeatAttCd4``(``:38``)
#:
#: 즉 후행 구간용 타입이 아예 따로 선언돼 있고
#: (``TicketReservationInSrcarTrailing.java:24``, 필드는 ``:29-30``
#: ``txtSeatNo``/``txtSrcarNo`` — 선행 쪽 ``TicketReservationInSrcar.java:23``
#: 의 ``:28-29`` 와 같은 모양), "trailing2" 나 셋째 접미사는 없습니다.
#: 구간 수는 ``txtJrnyCnt``(``:42``)로 실립니다. 이름은 전부 **읽힘**.
KORAIL_MAX_JOURNEY_LEGS = 2

# ---------------------------------------------------------------------------
# NetFunnel — 가상 대기열. 호스트가 따로.
#
# 7.0.6 근거는 두 자리입니다.
#
# (1) 선언: com/korail/talk/common/NetworkConstants.java 의 중첩 object
#     Netfunnel(:80-99). 정수는 그대로 읽힙니다:
#       PORT    = 443   (:82)   ← https 기본 포트
#       RETRY   = 1     (:83)
#       TIMEOUT = 3     (:84)   ← 아래 타임아웃 상수의 직접 근거
#     문자열은 AlienGuard 로 보호됐지만 byte[] 길이가 전부 맞습니다
#     (길이 일치):
#       PROTOCOL   :85  len 5   ← "https"
#       HOST       :86  len 17  ← "nf.letskorail.com"
#       SERVICE_ID :87  len 9   ← "service_1"
#       ACTION_ID  :88  len 5   ← "act_8"
#
# (2) 주입: KorailTalkApplication.setNetFunnel()(:361-389), onCreate() 가
#     :410 에서 부릅니다. 복호화된 문자열을 Property 세터로 순서대로 넘기는데
#     그 순서와 byte[] 길이가 (1) 과 정확히 겹칩니다:
#       :363-367  len 5   (protocol)
#       :368-372  len 17  (host)
#       :373-376  443     ← 평문 정수 리터럴, 읽힘
#       :377-381  len 9   (serviceID)
#       :382-386  len 5   (actionID)
#       :387      {3}     ← setTimeout(3), 읽힘
#       :388      {1}     ← setRetry(1),   읽힘
#     세터 자체는 AppSuitLinker6 디스패처로 가려져 이름이 안 보이지만,
#     인자 순서·타입·길이가 com/netfunnel/api/Property.java 의 세터 순서
#     (setProtocol :85, setHost :69, setPort :77, setServiceID :133,
#     setActionID :141, setTimeout :101, setRetry :117)와 일치합니다.
#
# 호스트 "nf.letskorail.com" 자체는 7.0.6 어디에도 평문으로 없습니다 —
# Property 의 컴파일된 기본값은 KORAIL 이 아니라 SDK 벤더 쪽
# "nf2.netfunnel.co.kr"(Property.java:11) 입니다. 따라서 이 호스트 값은
# 길이 17 이라는 제약 + 실서버 동작으로 뒷받침되고, 리터럴 자체는 보호됨.
#
# 경로 "ts.wseq" 는 평문으로 읽힙니다 — com/netfunnel/api/Property.java:17
# 의 query_ = "ts.wseq"(SDK 기본값이며 KORAIL 이 덮어쓰지 않음). 같은 파일
# :18 의 service_id_ = "service_1" 도 평문인데, 이것은 SDK 기본값이 마침
# KORAIL 의 값과 같다는 뜻입니다 — 위 (1)/(2) 의 길이 9 와도 맞습니다.
#
# 앞의 슬래시는 SDK 가 붙입니다. com/netfunnel/api/http/URL.java 의
# URL.make(Property)(:135-137)가
# property.getQuery() 를 **path** 자리에 넘기고(make(...) :126-133 의
# setPath(str3)), toString()(:75-108)이 "protocol://host" 뒤에 "/"(:98) +
# path(:101) + "?" + query(:107) 를 이어 붙입니다. 포트는 https+443 이면
# 생략됩니다(:90-93). 결과가 https://nf.letskorail.com/ts.wseq?... 입니다 —
# 그래서 이 라이브러리는 슬래시를 경로 상수에 미리 박아 둡니다.
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
#: 대기열 요청 하나의 타임아웃(초). 7.0.6 근거 둘 다 **읽힘** —
#: ``NetworkConstants.java:84`` 의 ``TIMEOUT = 3`` 과
#: ``KorailTalkApplication.java:387`` 의 ``setTimeout``에 넘기는 ``{3}``.
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0
#: 실패한 대기열 요청의 재시도 횟수(첫 시도 제외). 7.0.6 근거 **읽힘** —
#: ``NetworkConstants.java:83`` 의 ``RETRY = 1`` 과 ``KorailTalkApplication.java:388``
#: 의 ``setRetry``에 넘기는 ``{1}``. SDK 는 실패한 시도 뒤 그 시도가 시작된 때부터
#: 타임아웃(3초)이 찰 때까지 기다렸다가 다시 보냅니다(``Netfunnel.java:352-363``,
#: ``Property.java:16`` 의 ``wait_retry_ = true``).
KORAIL_NETFUNNEL_RETRY = 1


class KorailNetFunnelAction(StrEnum):
    """대기열 액션 id(``aid``).

    7.0.6 정본은 ``NetworkConstants.Netfunnel``
    (``com/korail/talk/common/NetworkConstants.java:80-99``)의 액션 상수
    일곱 개입니다. 리터럴은 AlienGuard 런타임 복호화라 평문으로 보이지 않고,
    이름별 ``byte[]`` 길이가 아래 값과 맞습니다(**길이 일치**):

    ====================================  ====  ========
    7.0.6 상수                             len   이 enum
    ====================================  ====  ========
    ``ACTION_ID`` (``:88``)                  5   ``act_8``
    ``ACTION_PEAK_SEASON_ID`` (``:91``)      7   ``act_8_2``
    ``ACTION_PRODUCT_ID`` (``:92``)          5   ``act_6``
    ``ACTION_RESERVE_ID`` (``:89``)          6   ``act_14``
    ``ACTION_PAY_ID`` (``:90``)              6   ``act_18``
    ``ACTION_RESERVATION_TICKET_ID``         6   ``act_21``
    (``:94``)
    ``ACTION_TEST_ID`` (``:93``)             5   ``act_4``
    ====================================  ====  ========

    같은 길이끼리(5: ``act_8``/``act_6``/``act_4``, 6: ``act_14``/``act_18``/
    ``act_21``)는 길이로 가려지지 않습니다. 호출부도 상수를 참조하지 않고 보호된
    문자열을 직접 넘기므로, 어느 호출부가 어느 값인지는 **호출부 메서드 이름으로
    추정**한 것입니다. 호출부 목록은
    :data:`~korail_mobile_api.netfunnel.KORAIL_NETFUNNEL_GATES` 에 있습니다.
    """

    #: 일반 열차조회. 조회 액션의 기본값 — 달력이 없거나 성수기가 아닌 날
    #: (``TrainScheduleViewModel.java:5225-5234``). ``KorailTalkApplication.java:382-386``
    #: 이 Property 에 넣는 기본 aid 도 len 5 입니다.
    INQUIRY = "act_8"
    #: 성수기 열차조회. ``RunDateOutItem.isPeakSeason()`` 이 참인 날
    #: (``TrainScheduleViewModel.java:5225-5229``, 판정은 ``bizDdStgCd`` 를 보호된
    #: 코드값과 비교 — ``RunDateOutItem.java:516-523``).
    PEAK_SEASON_INQUIRY = "act_8_2"
    #: 상품(특가) 열차조회. ``specialOffer`` 가 있으면(``ACCOMPANY_4`` 제외) 조회
    #: 액션이 따로 고른 len 5 문자열이 됩니다(``TrainScheduleViewModel.java:5213-5215``).
    #: 그 문자열이 ``ACTION_PRODUCT_ID`` 라는 것은 **추정(미검증)** 입니다.
    PRODUCT = "act_6"
    #: 예약(회원 ``certification.TicketReservation``·좌석배정 ``reservation.seatAssign.do``
    #: ·비회원 ``nonMember.NonMemTicket``). 호출부는 ``netFunnelTicketReservation``/
    #: ``netFunnelNonMemTicket`` 여섯 곳, 모두 len 6.
    RESERVE = "act_14"
    #: 결제(``payment.ReservationPayment`` 외). 호출부는 ``PayViewModel.java:6724``,
    #: ``FPayViewModel.java:795`` 의 ``executePayment``, len 6.
    PAY = "act_18"
    #: 예약내역 조회(``reservation.ReservationView``). 호출부는
    #: ``MyReservationViewModel.java:2528`` 의 ``reqReservationView``, len 6.
    RESERVED = "act_21"
    #: 테스트. 선언(``NetworkConstants.java:93``)만 있고 호출부는 없습니다.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """대기열 요청 종류.

    7.0.6 정본은 ``com/netfunnel/api/Command.java:4-11`` 의 ``Command``
    enum 입니다 — 이 패키지는 AlienGuard 가 걸려 있지 않아 **평문으로
    읽힙니다**:

    * ``CHK_ENTER(5002)``        — ``Command.java:6``
    * ``ALIVE_NOTICE(5003)``     — ``:7``
    * ``SET_COMPLETE(5004)``     — ``:8``
    * ``GET_TID_CHK_ENTER(5101)``— ``:9``
    * ``INIT(5105)``             — ``:10``
    * ``STOP(5106)``             — ``:11``

    이름과 값이 이 enum 여섯 항목과 그대로 일치합니다(``:5`` 의
    ``None(0)`` 만 여기 없음). 값은 ``value()``(``:19-21``)로 꺼내
    ``CommandClient`` 가 ``addParam("opcode", ...)`` 에 싣습니다.

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
#: DynaPath 토큰 허용 경로.
#:
#: 7.0.6 근거: ``network/interceptor/DynaPathInterceptor.java:40`` 의
#: ``public static final Set<String> STLhnr = SetsKt.setOf(...)`` — 여섯
#: 원소이고 각 원소가 AlienGuard 문자열입니다. 리터럴은 보호됐지만
#: ``byte[]`` 길이 다중집합이 ``{38, 41, 49, 49, 56, 58}`` 로 아래 여섯
#: 경로의 평문 길이와 **정확히** 같습니다:
#:
#: * 38 — ``/classes/com.korail.mobile.login.Login``
#: * 41 — ``/classes/com.korail.mobile.trn.prcFare.do``
#: * 49 — ``/classes/com.korail.mobile.nonMember.NonMemTicket``
#: * 49 — ``/classes/com.korail.mobile.seatMovie.ScheduleView``
#: * 56 — ``/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial``
#: * 58 — ``/classes/com.korail.mobile.certification.TicketReservation``
#:
#: 이 일치가 이 파일 머리말에 적은 "길이 일치" 등급의 **검증 기준**이기도
#: 합니다 — 여섯 개가 한꺼번에 맞을 확률로 보면 우연이 아닙니다. 같은
#: 파일 ``:34``/``:35`` 의 두 18바이트 문자열은 헤더 이름
#: ``x-dynapath-m-token``(18자)과 길이가 맞습니다.
#: 함께 있는 ``:41`` 의 ``Set<Integer> STLhns = {-1203, -1406, -2000,
#: -8005, -8201, -8202, -8203}`` 은 **평문으로 읽히는** 차단 코드 집합인데
#: 이 라이브러리에는 대응 상수가 없습니다.
#:
#: 7.0.6 은 ``Set`` 이라 순서가 없습니다. 아래 순서는 이 라이브러리의
#: 것이지 앱의 것이 아닙니다.
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
#: 허용목록보다 좁음 — 여기 있는 경로만 **전송 전에** 막습니다. 나머지는 보내지만,
#: 서버가 거절할 수 있습니다: 2026-09-24 라이브에서 토큰 없는 열차조회
#: (``ScheduleView``)가 ``MACRO ERROR`` 로 거절됐습니다(예전 관측은 성공이었음).
DYNAPATH_REQUIRED_PATHS = frozenset({KORAIL_LOGIN_PATH})
