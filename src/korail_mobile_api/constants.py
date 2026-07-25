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
