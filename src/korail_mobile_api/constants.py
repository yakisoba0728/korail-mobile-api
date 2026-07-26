from enum import StrEnum

KORAIL_BASE_URL = "https://smart.letskorail.com"
KORAIL_DEVICE_ANDROID = "AD"
KORAIL_API_VERSION = "250601003"
KORAIL_APP_KEY = "korail1234567890"
KORAIL_TIMEOUT_SECONDS = 60.0
KORAIL_USER_AGENT = "korail-mobile-api/0.2.0"
KORAIL_DEFAULT_DEVICE_NAME = "Android"
# The DynaPath "os" field is Build.VERSION.RELEASE — the marketing release
# string, e.g. "15" for Android 15 — NOT Build.VERSION.SDK_INT:
# b/C1229b.java:128-131 puts Build.VERSION.RELEASE under Constants.OS.
# This previously held "35", the SDK int, which is a different value that the
# app only ever sends as the common-code form's integer OSVersion field
# (CommonService.java:32) — see KORAIL_DEFAULT_ANDROID_SDK_INT below.
KORAIL_DEFAULT_ANDROID_OS_RELEASE = "15"
KORAIL_DEFAULT_DEVICE_WIDTH = 1080
KORAIL_DEFAULT_DEVICE_HEIGHT = 2400
# Build.VERSION.SDK_INT. Sent as the integer @Field("OSVersion") on
# common.code.do (CommonService.java:32). 35 is the SDK level of Android 15,
# so this and KORAIL_DEFAULT_ANDROID_OS_RELEASE describe the same platform with
# two different numbers; they are not interchangeable.
KORAIL_DEFAULT_ANDROID_SDK_INT = 35

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
    """The cabin class a request asks for (``txtPsrmClCd`` / ``psrmClCd``).

    ``K4/o.java:7-9`` declares three: ``GENERAL("일반실", "1")``,
    ``SPECIAL("특실", "2")`` and ``ALL``. Only the first two are ever bookable.
    The booking screen turns the user's chosen tab into exactly one of them --
    ``U4/a.java:88`` (``getSelectSeatTypeCode``) returns
    ``(seatType == 0 ? GENERAL : SPECIAL).getCode()`` -- and ``c5/b.java:72``
    feeds that value straight into ``OSeat.setPsrmClCd``, i.e. into the
    ``txtPsrmClCd1`` this package sends. ``ALL`` is a search-side wildcard
    (``u4/b.java:101`` sends it on ScheduleView) and is not a cabin one can be
    seated in, so it is deliberately absent here.
    """

    GENERAL = "1"
    SPECIAL = "2"


class KorailReservationJobType(StrEnum):
    """``txtJobId``: which of the booking screen's actions a hold performs.

    All three POST the same route
    (``certification.TicketReservation``, ``CertificationService.java:52-54``)
    with the same passenger, seat and journey maps; the job id -- and, for
    :attr:`SEAT_DESIGNATED`, one extra ``OSrcar`` map -- is the whole
    difference.

    * :attr:`IMMEDIATE` (``"1101"``) is what ``C5/a.java:59`` writes while
      building the journey map, i.e. the default the booking screen carries
      until the user does something else. ``C5/a.java:118`` then calls
      ``getOSrcar().clear()``, so an ordinary hold transmits no seat-designation
      keys at all -- ``OSrcar`` reaches Retrofit as a ``@FieldMap``
      (``CertificationService.java:54``) and an empty map contributes no fields.
      srtgo's unconditional ``txtSrcarCnt="0"`` (``ktx.py``) is therefore a
      shape the app never sends.
    * :attr:`STANDBY` (``"1102"``) is 예약대기, set when the user taps the
      second booking button (``DirectInquiryActivity.java:434``).
    * :attr:`SEAT_DESIGNATED` (``"1103"``) is set the moment the seat map
      returns a selection (``C5/a.java:143-146``): the activity copies
      ``SEAT_SELECT_DATA`` into a fresh ``OSrcar`` and switches the job id.
    """

    IMMEDIATE = "1101"
    STANDBY = "1102"
    SEAT_DESIGNATED = "1103"


# The exact h_wait_rsv_flg value that makes a train standby-eligible.
#
# Two characters, a SPACE then a 9. The app compares the search row's
# h_wait_rsv_flg against this literal and nothing else --
# analysis/apktool/smali/U4/a.smali:1250-1290, inside the U4.a.b() train-row
# bundler that jadx could not decompile (U4/a.java:52-57 is a stub). The smali
# reads getH_wait_rsv_flg() into v4, then:
#
#     if (N.isNotNull(v4) && " 9".equals(v4) && cVar == K4.c.RSV_DEFAULT)
#         waitEligible = true
#
# and at :1969-1981 writes bundle.putBoolean("wait", isStandardCabin &&
# waitEligible). That bundle bool is the ONLY input to a5/k.java:120-126's
# G0(), which in turn is the only thing that enables the 예약대기 button
# (a5/u.java:371 -> :401). h_gen_rsv_cd is never consulted for standby, so
# "sold out" is not the app's test; this flag is.
#
# korail2 (korail2.py:196-199) describes the same field as -2/9/0. Only the 9
# has any support in this app, and its wire spelling is right-aligned in two
# characters, which is why the literal carries a leading space.
KORAIL_STANDBY_WAIT_FLAG = " 9"

# The reservation-response message code that means "this hold is a standby
# (예약대기) hold, go collect the notify options".
# com/korail/talk/ui/inquiry/rir/orr/a.java:222-225 routes to
# ReservationWaitActivity on exactly this code and nothing else. It is NOT a
# failure code: strResult is still SUCC and a PNR is still returned.
KORAIL_STANDBY_HOLD_MESSAGE_CODE = "IRR000014"


# The most passengers one reservation may carry. The booking screen's passenger
# picker is the authority: m5/d.java:32-33 (the picker the main booking flow
# instantiates, MainBookingActivity.java:832/1180/1184) sets min 0 / max 9, and
# m5/c.java:250-252 refuses a further increment once getTotalCount() reaches
# that max. Every individual type is capped at 9 as well (m5/c.java:110-118),
# so 9 is the ceiling on the total and on any single row. The same 9 already
# bounds this package's seat-inventory passenger_count.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9

# ---------------------------------------------------------------------------
# NetFunnel — the virtual waiting room, on its own host.
#
# Every value here is read off KTApplication.g(), which configures the queue SDK
# at application start (analysis/jadx/sources/com/korail/talk/application/
# KTApplication.java:79-85):
#
#     defaultInstance.setProtocol(Constants.SCHEME);        // "https"
#     defaultInstance.setHost("nf.letskorail.com");
#     defaultInstance.setPort(U.DEFAULT_PORT_SSL);          // 443
#     defaultInstance.setServiceID(g.NETFUNNEL_SERVER_ID);  // "service_1"
#     defaultInstance.setActionID(g.NETFUNNEL_ACTION_ID);   // "act_8"
#     defaultInstance.setTimeout(3);
#
# The path is the ONE field whose name lies about it: T6/h.java:31 holds
# `ts.wseq` in the field its getter calls getQuery(), and U6/c.make(protocol,
# host, port, query) passes that straight into setPath (U6/c.java:26-33). The
# assembled URL (U6/c.java:82-108) is therefore https://nf.letskorail.com/ts.wseq
# with the port elided because it is 443 — there is no query component until
# U6/a.java appends the parameters.
#
# This host is DELIBERATELY not part of KORAIL_BASE_URL's origin assertion and
# never will be: assert_korail_origin pins the API to smart.letskorail.com, and
# assert_korail_netfunnel_origin pins the queue here. Neither client can reach
# the other's host.
# ---------------------------------------------------------------------------
KORAIL_NETFUNNEL_URL = "https://nf.letskorail.com"
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
# KTApplication.java:85, `setTimeout(3)` — seconds, applied to both the connect
# and the socket timeout (U6/a.java:150-153). Far tighter than the 60s the API
# client uses, which is the app's own judgement that a waiting room that does not
# answer promptly is not worth waiting on.
KORAIL_NETFUNNEL_TIMEOUT_SECONDS = 3.0


class KorailNetFunnelAction(StrEnum):
    """The queue action ids, all eight, from ``K4/g.java:43-51``.

    An action is a separate line: the server meters ``act_8`` and ``act_8_2``
    independently even though both are 열차조회 on ``service_1``. That is the
    entire point of :attr:`PEAK_SEASON_INQUIRY`.

    Six of the eight have call sites in the APK; the trailing comments say which,
    and say plainly where there is none. Being declared but unwired is a fact
    about v6.5.0, not a reason to hide the constant — the server side of an
    action exists whether or not this app version reaches for it.
    """

    #: 일반 조회. Also the SDK-wide default (``KTApplication.java:84``) and what
    #: the in-app queue test screen uses
    #: (``com/korail/talk/test/NetfunnelTestActivity.java:54``).
    INQUIRY = "act_8"
    #: 성수기 조회 — a SEPARATE queue for peak-season departure dates, chosen at
    #: ``b5/c.java:439``, ``MainBookingActivity.java:749`` and
    #: ``OldMainBookingActivity.java:321``. See
    #: :func:`~korail_mobile_api.netfunnel.inquiry_action`.
    PEAK_SEASON_INQUIRY = "act_8_2"
    #: 상품(관광열차) 조회 — ``b5/c.java:439``, taken when the request is a
    #: ``ProductTrainInquiryRequest``, ahead of the peak-season test.
    PRODUCT = "act_6"
    #: 예약 — ``DirectInquiryActivity.java:442`` (예약대기), :469 (일반 예약)
    #: and :499 (the 공무원 인증 variant).
    RESERVE = "act_14"
    #: 결제 — ``B6/AbstractC1269e.java:1046`` and ``B6/C1270f.java:232``.
    PAY = "act_18"
    #: 예약목록 — ``com/korail/talk/ui/menu/ReservedTicketActivity.java:553``.
    RESERVED = "act_21"
    #: 환불. Declared at ``K4/g.java:47`` and referenced by NOTHING in the APK —
    #: the refund flow attaches no queue gate at all.
    REFUND = "act_22"
    #: 테스트. Declared at ``K4/g.java:50`` and likewise referenced by nothing;
    #: note that the app's own NetFunnel test screen gates on ``act_8`` instead.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """``T6/c.java:6-11`` — the queue request types, verbatim.

    Byte-for-byte the same table SRT's ``netfunnel.js`` declares, which is the
    evidence that the two apps embed two client SDKs for one product (STCLab
    NetFunnel) rather than talking to two different systems.

    :attr:`ALIVE_NOTICE`, :attr:`INIT` and :attr:`STOP` are declared here because
    the app declares them, and are deliberately NOT implemented.
    ``ALIVE_NOTICE`` exists to keep a visible waiting-room popup alive
    (``T6/g.java:517-527``) and this library renders none; ``Init`` and ``Stop``
    are administrative and the app's own SDK refuses them outright, throwing
    ``ErrorNotSupport`` without touching the network
    (``T6/d.java:115-121``).
    """

    CHK_ENTER = "5002"
    ALIVE_NOTICE = "5003"
    SET_COMPLETE = "5004"
    GET_TID_CHK_ENTER = "5101"
    INIT = "5105"
    STOP = "5106"


DYNAPATH_HEADER_NAME = "x-dynapath-m-token"
DYNAPATH_ALLOWLIST_PATHS = frozenset(
    {
        "/classes/com.korail.mobile.certification.TicketReservation",
        "/classes/com.korail.mobile.nonMember.NonMemTicket",
        "/classes/com.korail.mobile.seatMovie.ScheduleView",
        "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial",
        "/classes/com.korail.mobile.trn.prcFare.do",
        "/classes/com.korail.mobile.login.Login",
    }
)
