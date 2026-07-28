"""앱에서 그대로 옮겨 온 상수 — 엔드포인트, 기기 기본값, 코드값.

여기 있는 값은 대부분 앱 v6.5.0 의 디컴파일 결과에서 읽은 것이고, 각 값
옆에 그 근거가 ``파일:줄`` 로 붙어 있습니다. 값을 바꾸면 서버가 보는 요청의
모양이 바뀝니다.

닫힌 코드 집합은 :class:`StrEnum` 으로 둡니다 —
:class:`KorailSeatClass`, :class:`KorailReservationJobType`,
:class:`KorailNetFunnelAction`, :class:`KorailNetFunnelOpcode`.
"""

from enum import StrEnum


KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
#: DynaPath 토큰의 ``dm`` 필드, 즉 ``Build.MODEL``(``b/C1229b.java:132``).
#: 앱이 정한 값이 아니라 앱이 돌고 있는 단말이 무엇이냐일 뿐이므로, 기본값을
#: 특정 기종 대신 일부러 일반적인 문자열로 둡니다. 기종을 못 박으면(srtgo 는
#: ``"SM-S928N"`` 을 씁니다) 화면 크기와 SDK 레벨까지 그 기종과 맞아야 하는데
#: 그 조합을 확정할 근거가 없습니다. 실제 기기로 고정하려면
#: :func:`~korail_mobile_api.live.build_config_from_env` 를 쓰면 됩니다.
#:
#: DynaPath 의 ``st`` 필드와 헷갈리지 않아야 합니다. 그쪽은 따로 리터럴
#: ``"Android"`` 입니다(``C1229b.java:135``).
KORAIL_DEFAULT_DEVICE_NAME = "Android"
#: DynaPath 토큰의 ``os`` 필드, 즉 ``Build.VERSION.RELEASE`` — 안드로이드 15
#: 면 ``"15"`` 인 마케팅 릴리스 문자열입니다(``b/C1229b.java:128-131``).
#: ``Build.VERSION.SDK_INT`` 가 아닙니다. SDK 정수는
#: :data:`KORAIL_DEFAULT_ANDROID_SDK_INT` 쪽입니다.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "15"
KORAIL_DEFAULT_DEVICE_WIDTH = 1080
KORAIL_DEFAULT_DEVICE_HEIGHT = 2400
#: ``Build.VERSION.SDK_INT``. ``common.code.do`` 의 정수 ``@Field("OSVersion")``
#: 로 나갑니다(``CommonService.java:32``). 35 는 안드로이드 15 의 SDK 레벨이라
#: :data:`KORAIL_DEFAULT_ANDROID_OS_RELEASE` 와 같은 플랫폼을 다른 숫자로
#: 가리킵니다. 서로 바꿔 쓸 수 없습니다.
KORAIL_DEFAULT_ANDROID_SDK_INT = 35


def build_dalvik_user_agent(*, os_release: str, device_model: str) -> str:
    """안드로이드 플랫폼 기본 User-Agent 를 앱이 보내는 모양으로 만듭니다.

    ``com.korail.talk`` 는 User-Agent 를 하드코딩하지 않습니다. Retrofit v1 을
    ``UrlConnectionClient``/``HttpURLConnection`` 위에서 쓰므로
    (``ExecuteDao.java:7-11``) 서버가 보는 것은 플랫폼이 붙이는 Dalvik
    문자열이고, 그것을 여기서 만듭니다.

    이 문자열을 적는 곳은 여기 하나뿐입니다. 기본 설정과
    :func:`~korail_mobile_api.live.build_config_from_env` 가 서로 다른 모양을
    보내는 일을 막기 위해서입니다. 두 인자를 키워드 전용으로 한 것은
    ``(os_release, device_model)`` 과 그 반대가 둘 다 그럴듯해서, 뒤바꿔도
    맞아 보이는 헤더가 나오기 때문입니다.

    진짜 플랫폼 문자열에는 끝에 ``Build/<id>`` 도 붙습니다
    (``Dalvik/2.1.0 (Linux; U; Android 13; SM-S928N Build/UP1A.231005.007)``).
    여기서는 뺐습니다 — 실제로 로그인이 된 것이 이 네 조각짜리 형태이고, 기기
    모델과 맞지도 않는 빌드 id 를 지어내면 검증 못 할 주장이 하나 늘 뿐입니다.
    """
    return f"Dalvik/2.1.0 (Linux; U; Android {os_release}; {device_model})"


#: 기본 ``User-Agent``. 적어 넣은 값이 아니라
#: :func:`build_dalvik_user_agent` 로 **유도된** 값입니다.
#:
#: Python 패키지 이름이 든 User-Agent 로는 로그인이 거절됩니다. 진짜 앱은
#: 파이썬 패키지 이름을 대지 않으므로, 그것은 ``smart.letskorail.com`` 으로
#: 가는 요청이 실을 수 있는 가장 티 나는 값입니다.
#:
#: 여기 박히는 기기명과 릴리스는 DynaPath 토큰의 ``dm``/``os`` 필드가 싣는
#: 것과 같은 두 상수에서 옵니다. 유도하는 이유가 그것입니다 — 한 요청 안에서
#: User-Agent 와 토큰이 서로 다른 기기를 주장하면, 그것은 무해한 불일치가
#: 아니라 둘이 서로 다른 데서 만들어졌다는 신호입니다.
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
    """요청이 지목하는 객실 등급(``txtPsrmClCd`` / ``psrmClCd``).

    ``K4/o.java:7-9`` 는 셋을 선언합니다 — ``GENERAL("일반실", "1")``,
    ``SPECIAL("특실", "2")``, ``ALL``. 예약이 되는 것은 앞의 둘뿐입니다.
    예매 화면은 사용자가 고른 탭을 이 둘 중 하나로 바꾸고
    (``U4/a.java:88``), 그 값이 그대로 ``OSeat.setPsrmClCd`` 를 지나
    이 패키지가 보내는 ``txtPsrmClCd1`` 이 됩니다(``c5/b.java:72``).

    ``ALL`` 은 검색 쪽 와일드카드(``u4/b.java:101``)이지 앉을 수 있는 객실이
    아니라서 여기 없습니다.
    """

    GENERAL = "1"
    SPECIAL = "2"


class KorailReservationJobType(StrEnum):
    """``txtJobId`` — 예매 화면의 어느 동작으로 잡는 예약인지.

    넷 다 같은 경로(``certification.TicketReservation``,
    ``CertificationService.java:52-54``)에 같은 승객·좌석·여정 맵을 실어
    보냅니다. 차이는 job id 하나, 그리고 :attr:`SEAT_DESIGNATED` 일 때 붙는
    ``OSrcar`` 맵 하나뿐입니다.

    * :attr:`IMMEDIATE`(``"1101"``) — 예매 화면이 기본으로 들고 있는 값
      (``C5/a.java:59``). 곧이어 ``getOSrcar().clear()`` 를 부르므로
      (``:118``) 평범한 예약은 좌석지정 키를 아예 싣지 않습니다. 빈 맵은
      ``@FieldMap`` 으로 나가면 필드가 하나도 되지 않기 때문입니다. srtgo 가
      무조건 붙이는 ``txtSrcarCnt="0"`` 은 앱이 보내지 않는 모양입니다.
    * :attr:`STANDBY`(``"1102"``) — 예약대기. 두 번째 예매 버튼을 누르면
      설정됩니다(``DirectInquiryActivity.java:434``).
    * :attr:`SEAT_DESIGNATED`(``"1103"``) — 좌석 선택이 돌아오는 순간
      설정됩니다(``C5/a.java:143-146``). 선택 결과를 새 ``OSrcar`` 에
      옮기면서 job id 를 바꿉니다.
    * :attr:`MERGE_STANDING`(``"1202"``) — 입석+좌석 예매. 병합예약을
      이루는 두 예약 중 **첫 번째** 입니다. job id 만 다를 뿐 평범한 단일구간
      폼입니다(``a5/u.java:394-397``,
      ``DirectInquiryActivity.java:448-451``). 실제로 병합인 두 번째 예약은
      :data:`KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` 쪽을 참조하면 됩니다.
    """

    IMMEDIATE = "1101"
    STANDBY = "1102"
    SEAT_DESIGNATED = "1103"
    MERGE_STANDING = "1202"


#: 열차가 예약대기 대상이 되는 ``h_wait_rsv_flg`` 값. 두 글자, **공백 다음
#: 9** 입니다.
#:
#: 앱은 검색 행의 ``h_wait_rsv_flg`` 를 이 리터럴하고만 비교합니다
#: (``smali/U4/a.smali:1250-1290``. jadx 가 풀지 못한 ``U4.a.b()`` 안이라
#: 바이트코드에서 읽었습니다). 그 결과가 ``bundle.putBoolean("wait", ...)`` 로
#: 실리고(:1969-1981), 그 불리언이 예약대기 버튼을 켜는 유일한 입력입니다
#: (``a5/k.java:120-126`` → ``a5/u.java:371`` → :401).
#:
#: 예약대기 판정에 ``h_gen_rsv_cd`` 는 쓰이지 않습니다 — 매진 여부가 아니라
#: 이 플래그가 기준입니다. 두 칸 오른쪽 정렬이라 리터럴 앞에 공백이 붙습니다.
KORAIL_STANDBY_WAIT_FLAG = " 9"

#: "이 예약은 예약대기다, 알림 옵션을 받아 가라"를 뜻하는 예약 응답 메시지
#: 코드. ``ui/inquiry/rir/orr/a.java:222-225`` 는 오직 이 코드에서만
#: ``ReservationWaitActivity`` 로 넘어갑니다.
#:
#: 실패 코드가 아닙니다. ``strResult`` 는 여전히 ``SUCC`` 이고 PNR 도
#: 나옵니다.
KORAIL_STANDBY_HOLD_MESSAGE_CODE = "IRR000014"

#: 할인카드(N카드) 하나에 등록할 수 있는 최대 구간 수.
#:
#: 앱은 구간 수마다 예매 Activity 를 따로 두고 셋에서 멈춥니다
#: (``NCard1SectionBookingActivity`` ~ ``NCard3SectionBookingActivity`` 와
#: 각각의 v2). ``K4/f.java:5-11`` 도 ``SECTIONONE``/``TWO``/``THREE`` 만
#: 선언하고 넷째가 없으며, 네 구간짜리 상품코드도 없습니다.
KORAIL_MAX_DISCOUNT_CARD_SECTIONS = 3

#: "이 좌석은 할인카드(N카드)로 산다"를 뜻하는 할인종류 코드. 앱이 이 값을
#: 쓰는 곳은 ``w4/a.java:100`` 하나, 되읽는 곳은 ``t4/a.java:59-61`` 의
#: ``isNCard()`` 하나뿐입니다.
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"

#: N카드 예약의 ``txtMenuId``. 평범한 예매 화면은 ``"11"`` 을 보내고
#: (``w4/a.java:115``), 좌석지정 화면은 ``"A2"`` 를 얹습니다
#: (``SeatAssignBookingActivity.java:159``. 정기권이면 ``"A1"``).
#: 승객 블록 밖에서 N카드 예약이 바꾸는 스칼라는 이 하나뿐입니다.
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


#: 예약 하나가 실을 수 있는 최대 승객 수.
#:
#: 예매 화면의 승객 선택기가 기준입니다. ``m5/d.java:32-33`` 이 최소 0·최대 9
#: 로 만들고, ``m5/c.java:250-252`` 는 합계가 그 최대에 닿으면 더 이상 늘리지
#: 않습니다. 개별 종류도 각각 9 가 상한이라(``m5/c.java:110-118``) 9 는
#: 합계의 상한이자 한 줄의 상한입니다.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9


# ---------------------------------------------------------------------------
# 환승 — 여정 하나, 구간 둘.
#
# K4/d.java:5-6 의 직통/환승 짝 `DIRECT_SQ_NO("직통", "1")` /
# `TRANSFER_SQ_NO("환승", "2")` 는 같은 두 코드로 세 가지 일을 한다.
#
#   * 검색 job id. WRD000061("직통열차가 없습니다")이 오면 앱은 같은
#     ScheduleView 질의를 `setRadJobId(TRANSFER_SQ_NO.getCode())` 만 바꿔
#     다시 보낸다 -- DirectInquiryActivity.java:284-296. 바이트코드에서도
#     확인했다(smali/…/DirectInquiryActivity.smali:1677-1689).
#   * `txtJrnyCnt`. 플래그가 아니라 구간 개수에서 유도한다 --
#     `setJrnyCnt((trainInfoArr.length == 1 ? DIRECT : TRANSFER).getCode())`,
#     C5/a.java:55.
#   * 구간별 `txtJrnySqno{i}` 의 씨앗 -- C5/a.java:61. S4/O.java:19-21 이
#     세 자리 0 채움을 하므로 전선에 나가는 값은 "1"/"2" 가 아니라
#     "001"/"002" 다.
KORAIL_DIRECT_ITINERARY_CODE = "1"
KORAIL_TRANSFER_ITINERARY_CODE = "2"

# `txtJrnyTpCd{i}`: K4/e.java:6-7. jadx 가 TRANSFER 의 코드를 값이 같은 다른
# 상수로 바꿔 놓아서 바이트코드에서 다시 읽었다 -- smali/K4/e.smali:40
# (DIRECT -> "11"), :68 (TRANSFER -> "14").
#
# C5/a.java:60 이 무엇을 보는지가 중요하다. 구간 루프 **안** 에 있지만
# 루프 인덱스가 아니라 배열 **길이** 를 본다. 그래서 환승은 두 구간 모두
# `txtJrnyTpCd = "14"` 를 싣는다 -- 1구간만 직통으로 남는 것이 아니다.
# 루프 안의 상수 삼항식은 jadx 가 가장 자주 잘못 접는 모양이라 이것도
# 바이트코드에서 확인했다(smali/C5/a.smali:306-338 은 매 회차마다
# `array-length` 를 다시 재고, 옆의 jrnySqNo 분기 :343 은 루프 인덱스를
# 본다. 둘은 실제로 다르다).
KORAIL_DIRECT_JOURNEY_TYPE_CODE = "11"
KORAIL_TRANSFER_JOURNEY_TYPE_CODE = "14"

# ---------------------------------------------------------------------------
# 병합예약 -- 열차 하나를 중간역에서 갈라 앞뒤를 다르게 앉히는 것. 환승이
# 아니고, C5/a.java 여정 루프의 세 번째 경우도 아니다. 폼을 만드는 곳 자체가
# 다르다.
#
# K4/e 의 나머지 두 멤버다. jadx 가 값이 같은 무관한 상수로 바꿔 놓아서 넷 다
# 바이트코드에서 다시 읽었다 -- smali/K4/e.smali:31-55:
#
#     DIRECT          "직통"       "11"
#     TRANSFER        "환승"       "14"
#     STANDING_SEAT_1 "병합 선행"  "21"
#     STANDING_SEAT_2 "병합 후행"  "22"
#
# 병합이 처음부터 끝까지 무엇인지:
#
#   1. 검색 행이 병합 대상인지는 S4/J.java:61-63 의 isMixedSeat() 이 정한다 --
#      아래 KORAIL_MERGE_SEAT_FLAGS_BY_CABIN. a5/u.java:378-380 이 행마다
#      계산하고 :394-397 이 예매 버튼을 "입석+좌석 예매"로 바꾸며 태그를
#      "1202" 로 단다.
#   2. 그 버튼은 **평범한 단일구간 직통 폼** 을 txtJobId="1202" 로 보낸다
#      (DirectInquiryActivity.java:448-451). 그 예약은 전 구간을 입석으로
#      산다.
#   3. KORAIL 의 답장 메시지에 리터럴 "<중간연결역 변경>"
#      (res/values/strings.xml:2018)이 들어 있다. 확인 화면은 메시지를 span
#      표로 그리고(res/values/arrays.xml:421-438) K6/C5956a.java:74-77 이 그
#      리터럴만 누를 수 있게 만든다. 즉 병합하자는 제안은 클라이언트가 아니라
#      **서버** 가 한다.
#   4. DirectInquiryActivity.java:294-296 이 그 결과에 답해
#      research.mergeSeatsC.do (이 패키지의
#      KorailClient.get_merge_seats_inquiry)로 좌석 재고가 바뀌는 역들을 묻고
#      좌석 연결역 선택 화면을 띄운다.
#   5. 확인하면 입석 예약을 취소하고(ReservationCancel → ReservationCancelChk,
#      DirectInquiryActivity.java:227-250) 그 한 열차 위의 **두 여정짜리 예약
#      하나** 로 다시 잡는다.
#
# 진짜 새로운 폼은 5 번뿐이고 C5/a.java 의 루프가 만들지 않는다.
# DirectInquiryActivity.java:576-601 이 따로 만들며 네 가지가 다르다. 전부
# smali/…/DirectInquiryActivity.smali:5580-6010 에서 확인했다.
#
#   * txtJrnyTpCd{i} 가 배열 길이가 아니라 루프 **인덱스** 를 본다(:5641).
#     1구간이 "21", 2구간이 "22" 다. 두 구간 모두 "14" 인 환승과 반대다.
#   * txtStndFlg 는 isStndSeat 에서 유도하지 않고 "Y" 로 못 박는다
#     (:5887-5891).
#   * 2구간의 객실 등급을 구간별로 읽지 않고 1구간의 txtPsrmClCd1 에서
#     복사한다(:5919-5983). 1구간에 없으면 일반실이 기본이다.
#   * setArvTm 호출이 아예 없어서 어느 구간에도 arvTm_ 키를 쓰지 않는다.
#     요청이 "1202" 예약 폼의 복제이고 OJrny 가 대체가 아니라 병합이라
#     (ReservationRequest.java:29-46, :158-160) 예약 때의 arvTm_1 -- 전
#     구간의 도착시각 -- 이 그대로 남고 arvTm_2 는 없다.
#
# txtJrnyCnt 는 "2", txtJobId 는 다시 "1101" 이며, txtJrnySqno 는 환승과
# 마찬가지로 루프 인덱스에서 "001"/"002" 로 나온다.
KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE = "21"
KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE = "22"

#: 검색 행을 병합 대상으로 만드는 ``h_yms_apl_flg`` 값을 객실 등급별로 모은
#: 표. 일반실은 ``"A"`` 또는 ``"G"``, 특실은 ``"A"`` 또는 ``"S"`` 입니다.
#:
#: ``S4/J.java:61-63`` 의 식을 등급마다 풀면 이 두 집합으로 접힙니다 — ``"M"``
#: 가지는 결국 ``"G".equals("M")`` 에 닿아 항상 거짓이라 아무것도 바꾸지
#: 않습니다. 키는 :class:`KorailSeatClass` 의 값이라 객실 코드와 어긋날 수
#: 없습니다.
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}

#: 예약 하나가 실을 수 있는 최대 구간 수. 둘입니다.
#:
#: 결정적인 근거는 폼에 3구간 철자가 아예 없다는 것입니다 — 세 번째 구간은
#: 무시되는 게 아니라 2구간을 조용히 덮어씁니다. ``OSeat.java:32-35`` 와
#: ``OSrcar.java:21-30`` 은 ``i == 1`` 이냐 아니냐로만 키를 나누고,
#: ``ReservationRequest.java:114-117`` 도 그 두 좌석 칸만 되읽습니다.
#:
#: 검색·선택 쪽도 둘을 넘기지 않습니다. ``a5/k.java:108-110`` 은 여정 빌더에
#: 넘길 배열을 한 행 아니면 정확히 두 행으로 만들고,
#: ``a5/k.java:156-170`` 은 환승 결과를 ``new Bundle[2]`` 로 묶으며,
#: ``a5/u.java:252-253`` 은 두 칸(둘째는 널 허용)으로만 넘깁니다.
KORAIL_MAX_JOURNEY_LEGS = 2

# ---------------------------------------------------------------------------
# NetFunnel -- 가상 대기열. 호스트가 따로다.
#
# 아래 값은 전부 앱 시작 때 대기열 SDK 를 설정하는 KTApplication.g() 에서
# 읽었다(com/korail/talk/application/KTApplication.java:79-85):
#
#     defaultInstance.setProtocol(Constants.SCHEME);        // "https"
#     defaultInstance.setHost("nf.letskorail.com");
#     defaultInstance.setPort(U.DEFAULT_PORT_SSL);          // 443
#     defaultInstance.setServiceID(g.NETFUNNEL_SERVER_ID);  // "service_1"
#     defaultInstance.setActionID(g.NETFUNNEL_ACTION_ID);   // "act_8"
#     defaultInstance.setTimeout(3);
#
# 이름이 내용을 속이는 필드가 하나 있다. T6/h.java:31 은 `ts.wseq` 를 게터
# 이름이 getQuery() 인 필드에 담아 두고, U6/c.make(...) 가 그것을 그대로
# setPath 로 넘긴다(U6/c.java:26-33). 조립된 URL 은
# https://nf.letskorail.com/ts.wseq 이고 포트는 443 이라 생략된다. U6/a.java
# 가 파라미터를 붙이기 전까지 질의 문자열은 없다.
#
# 이 호스트는 KORAIL_BASE_URL 의 오리진 검사에 들어가지 않는다.
# assert_korail_origin 이 API 를 smart.letskorail.com 에 못 박고,
# assert_korail_netfunnel_origin 이 대기열을 여기 못 박는다. 어느 클라이언트도
# 상대 호스트에 닿을 수 없다.
# ---------------------------------------------------------------------------
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
#: 대기열 타임아웃(초). ``KTApplication.java:85`` 의 ``setTimeout(3)`` 이며
#: 연결과 소켓 양쪽에 걸립니다(``U6/a.java:150-153``). API 클라이언트의
#: 60초보다 훨씬 짧습니다 — 빨리 답하지 않는 대기실은 기다릴 값어치가 없다는
#: 앱의 판단입니다.
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0


class KorailNetFunnelAction(StrEnum):
    """대기열 액션 id 여덟 개 전부(``K4/g.java:43-51``).

    액션 하나가 줄 하나입니다. ``act_8`` 과 ``act_8_2`` 는 둘 다 ``service_1``
    위의 열차조회지만 서버는 따로 계량합니다 — :attr:`PEAK_SEASON_INQUIRY` 가
    따로 있는 이유가 그것입니다.

    여덟 중 여섯만 APK 에 호출 지점이 있습니다. 선언만 되고 쓰이지 않는 것은
    앱 v6.5.0 의 사정일 뿐, 서버 쪽 액션은 이 앱이 부르든 말든 존재합니다.
    """

    #: 일반 조회. SDK 전역 기본값이기도 합니다(``KTApplication.java:84``). 앱
    #: 안의 대기열 시험 화면도 이것을 씁니다
    #: (``com/korail/talk/test/NetfunnelTestActivity.java:54``).
    INQUIRY = "act_8"
    #: 성수기 조회. 성수기 출발일에는 별도의 줄입니다(``b5/c.java:439``,
    #: ``MainBookingActivity.java:749``, ``OldMainBookingActivity.java:321``).
    #: :func:`~korail_mobile_api.netfunnel.inquiry_action` 참조.
    PEAK_SEASON_INQUIRY = "act_8_2"
    #: 상품(관광열차) 조회. 요청이 ``ProductTrainInquiryRequest`` 면 성수기
    #: 판단보다 먼저 이쪽으로 갑니다(``b5/c.java:439``).
    PRODUCT = "act_6"
    #: 예약. ``DirectInquiryActivity.java:442``(예약대기), :469(일반 예약),
    #: :499(공무원 인증 변형).
    RESERVE = "act_14"
    #: 결제. ``B6/AbstractC1269e.java:1046``, ``B6/C1270f.java:232``.
    PAY = "act_18"
    #: 예약목록. ``com/korail/talk/ui/menu/ReservedTicketActivity.java:553``.
    RESERVED = "act_21"
    #: 환불. ``K4/g.java:47`` 에 선언돼 있으나 APK 어디에서도 참조하지
    #: 않습니다 — 환불 흐름에는 대기열 게이트가 걸려 있지 않습니다.
    REFUND = "act_22"
    #: 테스트. ``K4/g.java:50`` 에 선언돼 있고 역시 참조하는 곳이 없습니다.
    #: 앱의 NetFunnel 시험 화면조차 ``act_8`` 로 겁니다.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """대기열 요청 종류(``T6/c.java:6-11``) 그대로.

    SRT 의 ``netfunnel.js`` 가 선언하는 표와 바이트 단위로 같습니다. 두 앱이
    서로 다른 시스템이 아니라 같은 제품(STCLab NetFunnel)의 클라이언트 SDK
    를 각각 품고 있다는 뜻입니다.

    :attr:`ALIVE_NOTICE`, :attr:`INIT`, :attr:`STOP` 은 앱이 선언하니 여기도
    선언만 하고 구현하지 않았습니다. ``ALIVE_NOTICE`` 는 화면에 떠 있는 대기열
    팝업을 살려 두는 용도인데(``T6/g.java:517-527``) 이 라이브러리는 아무
    화면도 그리지 않습니다. ``Init``/``Stop`` 은 관리용이고, 앱의 SDK 자신이
    네트워크에 닿지도 않고 ``ErrorNotSupport`` 를 던집니다
    (``T6/d.java:115-121``).
    """

    CHK_ENTER = "5002"
    ALIVE_NOTICE = "5003"
    SET_COMPLETE = "5004"
    GET_TID_CHK_ENTER = "5101"
    INIT = "5105"
    STOP = "5106"


DYNAPATH_HEADER_NAME = "x-dynapath-m-token"
KORAIL_LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
#: 앱이 DynaPath 토큰을 실어 보내는 경로. 켜져 있으면 여기에만 붙습니다.
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
#: 토큰 **없이는 통하지 않는** 경로. 꺼진 설정으로 부르면 전송 전에
#: :class:`~korail_mobile_api.errors.KorailDynaPathRequiredError` 로 막힙니다.
#:
#: 허용목록과 같지 않고 더 좁습니다. 토큰 없이 관측된 결과가 갈렸기
#: 때문입니다 — 검색을 비롯한 읽기는 토큰 없이 성공했고 ``login.Login`` 만
#: 거절당했습니다. 관측되지 않은 것을 막으면 잘 되던 읽기를 이 패키지가 끊는
#: 셈이므로, 근거가 있는 하나만 요구합니다. 다른 경로에서 거절이 관측되면
#: 여기 추가하면 됩니다.
DYNAPATH_REQUIRED_PATHS = frozenset({KORAIL_LOGIN_PATH})
