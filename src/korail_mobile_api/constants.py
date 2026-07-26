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

    They all POST the same route
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
    * :attr:`SEAT_DESIGNATED` (``"1103"``) is set the moment the seat map
      returns a selection (``C5/a.java:143-146``): the activity copies
      ``SEAT_SELECT_DATA`` into a fresh ``OSrcar`` and switches the job id.
    """

    IMMEDIATE = "1101"
    SEAT_DESIGNATED = "1103"


# The most passengers one reservation may carry. The booking screen's passenger
# picker is the authority: m5/d.java:32-33 (the picker the main booking flow
# instantiates, MainBookingActivity.java:832/1180/1184) sets min 0 / max 9, and
# m5/c.java:250-252 refuses a further increment once getTotalCount() reaches
# that max. Every individual type is capped at 9 as well (m5/c.java:110-118),
# so 9 is the ceiling on the total and on any single row. The same 9 already
# bounds this package's seat-inventory passenger_count.
KORAIL_MAX_PASSENGERS_PER_RESERVATION = 9

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
