from .redaction import redact_text


class KorailApiError(Exception):
    """Base error for KORAIL client failures."""

    def __init__(self, *args: object) -> None:
        super().__init__(
            *(
                redact_text(arg) if isinstance(arg, str) else arg
                for arg in args
            )
        )


class KorailTransportError(KorailApiError):
    """HTTP transport failed before an app-level response was parsed."""


class KorailProtocolError(KorailApiError):
    """The server response did not match the documented protocol."""


class KorailAuthError(KorailApiError):
    """Login or session authentication failed."""


class KorailSessionExpiredError(KorailAuthError):
    """The authenticated KORAIL session is no longer valid."""

    def __init__(
        self,
        code: str | None,
        message: str | None,
        *,
        raw: object | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'P058'}: "
            f"{redact_text(message or 'KORAIL session expired')}"
        )


class KorailDynaPathError(KorailApiError):
    """The KORAIL DynaPath layer rejected a request — the anti-macro refusal.

    "Retry is pointless right now; you were flagged, not merely throttled."

    This is what an anti-macro rejection looks like on this app, and the APK is
    unambiguous that it is a HEADER decision, not an ``h_msg_cd`` one.
    ``BaseDaoHelper`` inspects every response for a ``DynaPath-Result`` header
    and, when its value is negative, reads ``message`` out of the JSON body and
    parks it on the dao as ``macroShowDialog``
    (``analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:59-86``).
    The dispatcher then shows that string INSTEAD of running the normal
    ``h_msg_cd`` ladder at all
    (``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:632-634``;
    mirrored at ``analysis/jadx/sources/l4/h.java:401-404``). The token that
    earns the header is attached only when the server-set ``IS_MACRO_ACTIVE``
    flag is on AND the URL is one of six sensitive paths
    (``analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:25-47``).

    So there is NO anti-macro message code to classify. srtgo_plus asserts one
    — ``if "MACRO" in code or "MACRO" in msg`` (``srtgo/srtgo.py:756``), after
    which it clears its NetFunnel key and retries — but the substring ``MACRO``
    appears nowhere in this app as a server code or message; the only in-app
    occurrences are the client-side flag ``IS_MACRO_ACTIVE``
    (``analysis/jadx/sources/I4/a.java:14``) and the string resource
    ``macro_alert_message`` (``analysis/apktool/res/values/strings.xml:996``),
    which is the post-login advisory described below. That claim is therefore
    recorded as **third-party-attested only** and is not encoded.

    Separately, KORAIL also warns about macro use on a SUCCESSFUL login: when
    the login response carries ``notiTpCd`` in ``{"MC", "MM", "MS"}`` the app
    queues ``macro_alert_message`` as a post-login popup
    (``analysis/jadx/sources/S4/u.java:57-90``) — the login still succeeded.
    That is an advisory on a success, not a rejection, and deliberately raises
    nothing here.
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        raw: object | None = None,
    ) -> None:
        self.raw = raw
        super().__init__(
            redact_text(message or "KORAIL DynaPath request rejected")
        )


class KorailAuthContinuationRequired(KorailAuthError):
    """Login requires the app's WebView authentication continuation."""

    def __init__(self, redirect_url: str, post_data: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.post_data = post_data
        self.raw = raw
        super().__init__("KORAIL login requires WebView continuation")


class KorailAppError(KorailApiError):
    """The server returned an app-level failure response.

    Base of the app-level taxonomy. ``code`` is the server's ``h_msg_cd``
    verbatim and ``raw`` is the whole response, so a caller can always fall back
    to inspecting the code even for a failure this library has no subclass for —
    and so the map below can be grown from real traffic. Every subclass is a
    REFINEMENT: ``except KorailAppError`` still catches all of them.

    **A failure is still decided by ``strResult``, never by the code.** The app
    works the same way. Its dispatcher recognises ``SEMGTK``, ``P058``,
    ``SUPDATE``, ``WRC000288`` and (for one dao) ``S198``, and then — crucially
    — falls off the end of the ladder setting the error object to ``null``, so
    **any unrecognised ``h_msg_cd`` on a non-``FAIL`` response is delivered to
    ``onReceive()`` as a success**
    (``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:600-649``,
    the ``aVar = null`` at :629; mirrored at
    ``analysis/jadx/sources/l4/h.java:380-400``). Classification here therefore
    only ever REPLACES an exception that would already have been raised. It adds
    no new raise condition, which is what keeps a success-with-a-warning a
    success — see :class:`KorailNoResultsError` and the module notes at the
    bottom of this file.
    """

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip()
        )


class KorailNoResultsError(KorailAppError):
    """The request was accepted and simply matched nothing.

    "Retry is pointless; ask a different question." An empty result is not
    always an empty list on this server — several endpoints declare it as a
    ``FAIL`` envelope with a code.

    The app agrees it is not a real error: for these codes it registers
    ``setErrorMsgCdNotShowDialog`` so the generic error dialog is suppressed and
    the screen simply renders its empty view. ``WRG000000`` is registered that
    way at four sites —
    ``analysis/jadx/sources/com/korail/talk/ui/inquiry/CommutationInquiryActivity.java:182``,
    ``analysis/jadx/sources/com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java:313``,
    ``analysis/jadx/sources/G6/C5681a.java:66`` and
    ``analysis/jadx/sources/G6/C5683c.java:82`` — with the suppression itself
    enforced in
    ``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:326-337``.
    ``P114`` is handled on the success path as an "empty list plus a notice"
    state at
    ``analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1393``
    and
    ``analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java:763``.

    ``P100`` ("검색된 데이터가 없습니다." — an empty reservation history) and
    ``WRT300005`` ("조회자료가 없습니다." — an empty ticket list) are
    **live-observed by this repository, zero-hit in the APK**. They are already
    tolerated per-endpoint by
    :func:`~korail_mobile_api.read_parsers._validate_envelope`'s
    ``accepted_empty_codes``, which returns an empty result WITHOUT raising;
    mapping them here only covers the case where the same code reaches an
    endpoint that has not opted in. korail2 and srtgo group the same four codes
    (``korail2/korail2.py:521-527``, ``srtgo/srtgo/ktx.py:380-381``).
    """


class KorailNoDirectTrainError(KorailNoResultsError):
    """No direct train on this route, but a transfer itinerary exists.

    "Retry is pointless as asked; re-ask as a transfer search." ``WRD000061``.

    This is the app's own reading, and it is explicit. ``DirectInquiryActivity``
    intercepts the code before the generic error handler and shows a two-button
    dialog
    (``analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:614-633``);
    the confirm callback re-issues the *same* query with the job id switched to
    ``TRANSFER_SQ_NO``
    (``analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:284-296``).
    Behind the dialog it also renders the empty train list, which is why this
    subclasses :class:`KorailNoResultsError` rather than standing alone.

    korail2 files ``WRD000061`` under no-results with the comment
    "직통열차는 없지만, 환승으로 조회 가능합니다" (``korail2/korail2.py:524``) —
    a third-party claim that, unusually, the APK fully corroborates.
    """


class KorailSoldOutError(KorailAppError):
    """The inventory is gone; this train cannot be booked.

    "Retry is pointless for this train; pick another." ``ERR211161``.

    APK-confirmed at two independent sites, both of which replace the server
    text with the app's own sold-out string rather than showing ``h_msg_txt``:
    ``analysis/jadx/sources/com/korail/talk/ui/ticket/change/TCSOptionsActivity.java:551``
    and
    ``analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java:314``.
    That string is ``tss_dialog_no_left_seat`` =
    "잔여석이 부족하여 서비스를 제공할 수 없습니다."
    (``analysis/apktool/res/values/strings.xml:2043``). Both sites use the
    single-button alert, i.e. the app offers no way forward.

    korail2 maps sold-out to exactly ``{ERR211161}`` (``korail2/korail2.py:534``).
    srtgo adds ``IRT010110`` (``srtgo/srtgo/ktx.py:388``); that code is **0-hit
    across jadx sources, all three smali trees, ``analysis/raw`` and
    ``analysis/splits``**, so it is recorded as **third-party-attested only**
    and is NOT mapped. Note also that the app's *train list* decides sold-out
    from display strings, not codes — ``"매진"``/``"좌석부족"`` gate the booking
    button at ``analysis/jadx/sources/a5/u.java:354`` — so a sold-out train is
    normally never requested at all.
    """


class KorailSeatUnavailableError(KorailAppError):
    """The specific seat request cannot be honoured; the train may still be bookable.

    "Do not give up on this train — retry WITHOUT seat designation." Distinct
    from :class:`KorailSoldOutError`, and the app draws exactly that distinction
    by offering an alternative instead of a dead end.

    * ``WRI411345`` — ``tss_dialog_no_seat`` = "요청하신 좌석이 이미 판매되었습니다.
      시스템에서 좌석을 자동으로 배정받으시겠습니까?"
      (``analysis/apktool/res/values/strings.xml:2046``), shown as a two-button
      dialog whose second button is 임의 좌석 배정 (assign me any seat) —
      ``analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java:312-313``
      with the helper at :214-221. Contrast the single-button alert used for
      ``ERR211161`` three lines below it.
    * ``ERR911081`` — ``tss_dialog_no_seat_not_allowed_time`` = "좌석선택 가능
      시간이 지났습니다. 자동으로 좌석을 배정받으시고, 예약을 진행하겠습니까?"
      (``strings.xml:2047``), again a two-button auto-assign offer at
      ``analysis/jadx/sources/a5/k.java:215-221``. It is one of the codes the
      reservation daos suppress the generic dialog for (``analysis/jadx/sources/
      c5/a.java:178``, ``c5/b.java:133``, ``c5/c.java:132``).
    * ``WRT800176`` — ``tss_dialog_no_left_seat_not_time`` = "좌석변경 가능시간이
      아닙니다." (``strings.xml:2045``), at
      ``analysis/jadx/sources/com/korail/talk/ui/ticket/change/TCSOptionsActivity.java:557``.

    This matters directly to :meth:`~korail_mobile_api.client.KorailClient.reserve`,
    which can designate seats. The library still does not retry on your behalf —
    a retried reserve is a duplicate booking — so acting on this is the caller's
    choice.
    """


class KorailReservationRefusedError(KorailAppError):
    """The reservation was refused; the app sends the user to their existing bookings.

    "Retry is pointless as-is; look at what you already hold."
    ``WRR800029``, ``ERR911531``, ``ERR911051``.

    This is the most heavily attested cluster in the APK after ``P058``. Nine
    reservation call sites register the three codes together so the generic
    error dialog is suppressed — ``analysis/jadx/sources/c5/a.java:174-177``,
    ``c5/b.java:129-132``, ``c5/c.java:128-131``,
    ``analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/a.java:47-49``,
    ``.../rir/orr/DirectInquiryActivity.java:339-341``,
    ``.../booking/mainBooking/MainBookingActivity.java:338-340``,
    ``.../booking/mainBooking/OldMainBookingActivity.java:216-218``,
    ``.../reservation/BixbyReservationActivity.java:81-83`` and
    ``.../ticket/confirm/TicketListActivity.java:886-888`` — and five handlers
    then show the SERVER's own ``h_msg_txt`` and navigate onward:
    ``analysis/jadx/sources/a5/k.java:208-214`` (whose callback ``I0`` at :69-71
    starts ``ReservedTicketActivity``, the user's reservation list),
    ``MainBookingActivity.java:1605``, ``OldMainBookingActivity.java:966``,
    ``BixbyReservationActivity.java:63`` and ``TicketListActivity.java:1603``.

    The app never states WHY, so neither does this class: what the APK proves is
    that these three are a distinct reserve-path refusal routed to the existing
    reservations, not a generic error. ``message`` carries the server's own
    explanation.
    """


class KorailInvalidRequestError(KorailAppError):
    """The server rejected a field in the request we built; the fix is the input.

    "Retry is pointless; fix the payload." All three codes are this
    repository's own live observations and are **0-hit in the APK** — they are
    field-level validation replies the app's own screens cannot produce, because
    the app never sends the malformed values we deliberately sent:

    * ``WRG200018`` "입력값오류(PNR번호)" — a reservation-detail read against an
      account holding no reservations
      (``docs/api-status-by-service.md:205``);
    * ``WRT100002`` "창구번호미입력,미승인창구" — the refund ticket-detail read
      with no real ticket (``docs/api-status-by-service.md:451``);
    * ``WRT100124`` "반환번호를 확인해주세요" — the refund commission read, same
      cause (``docs/api-status-by-service.md:450``).

    Neither korail2 nor srtgo models this condition at all.
    """


class KorailNotEntitledError(KorailAppError):
    """The account is not entitled to the discount or product requested.

    "Retry is pointless; this account may not book that fare."
    ``ERR299943`` "예약할인이 지원되지 않습니다".

    **Live observation only — 0 hits anywhere in the APK.** It is a server-side
    business rule with no client-side counterpart, seen refusing a 청소년 fare
    booked alone and a 1~3급 장애 + 안내견 combination, on forms that otherwise
    matched the app byte for byte (``docs/MUTATION_HANDOFF.md:172-179``,
    ``CHANGELOG.md:57-60``). Distinguished from
    :class:`KorailInvalidRequestError` because the payload is well-formed: the
    request is refused for who is asking, not for what was sent.
    """


class KorailServiceUnavailableError(KorailAppError):
    """KORAIL declared the service itself unavailable. ``SEMGTK``.

    "Retry is pointless right now; the back end is down, not your request."

    The app checks this ahead of every other code and converts it into its
    offline-fallback error class ``R4.b``
    (``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:608-609``;
    mirrored at ``analysis/jadx/sources/l4/h.java:384-385``), which is dispatched
    to a two-button dialog offering the saved-ticket screen rather than the
    generic error alert
    (``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:298-301``,
    ``:358-366``). ``R4.b``'s default text is
    "인터넷 연결상태(WiFi, 4G, 5G)가 좋지 않습니다.\\n\\n저장된 승차권 화면으로
    이동하시겠습니까?" (``analysis/jadx/sources/R4/b.java:5-7``).
    """


class KorailAppUpdateRequiredError(KorailAppError):
    """The server refused this client version and demands an app update. ``SUPDATE``.

    "Retry is pointless at any interval; the client is what is rejected."

    ``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:613-619``
    gives this its own dialog, whose button handler sends the user to Google
    Play. It is the only code the app answers by leaving the app entirely.

    A caller seeing this should expect that
    :data:`~korail_mobile_api.constants.KORAIL_API_VERSION` — the ``Version``
    field this library sends on every request — has been superseded.
    """


class MutationNotAllowedError(KorailApiError):
    """A state-changing request was attempted without matching consent.

    Raised by ``require_mutation_consent`` when no ``MutationConsent`` is
    supplied, when the supplied object is not a ``MutationConsent``, or when
    the matching per-category ``allow_<category>`` opt-in is False. It fires
    before any request is built or sent, keeping mutations off by default.
    """


# ---------------------------------------------------------------------------
# h_msg_cd -> exception mapping
#
# CODES, NOT MESSAGE TEXT, because that is what the app does. Every branch in
# the dispatcher compares gethMsgCd() against a literal
# (BaseActivity.java:600-649); the app never substring-matches h_msg_txt, it only
# displays it, <br>-to-newline and all (:625). The one place the app reads Korean
# text at all is the TRAIN LIST, where "매진"/"좌석부족" in a row's display state
# gate the booking button (a5/u.java:354) -- a rendering decision about data we
# already parse, not an error classification.
#
# WHAT THIS MAP MAY NOT DO. It may only refine an exception that would already
# have been raised. Failure is decided by strResult (plus the app's own
# WRC000288), never by the code, and the app itself drops any unrecognised code
# on a non-FAIL response straight through to onReceive() as a success
# (BaseActivity.java:629, `aVar = null`). The app is full of codes that ride
# along with a success and must never become exceptions:
#
#   IRR000014  waitlist accepted -> starts ReservationWaitActivity
#              (ui/inquiry/rir/orr/a.java:223)
#   IRT800005  reservation succeeded with a notice; both dialog branches call the
#              same z2(response) continuation (ui/inquiry/rir/orr/a.java:142, :71)
#   WRS800036  per-leg advisory, purchase continues
#              (ui/reservation/confirm/activity/DReservationConfirmActivity.java:76)
#   IRZ000001 / S200   login success (S4/u.java:131)
#   IRT000000 / MRT200105  upgrade quote accepted (ui/push/SpecialRoomUpgradeActivity.java:55)
#
# and this repository has its own live proof: WRR664296 ("KTX/새마을호/ITX-청춘
# 열차의 경로 및 장애인(4-6급)할인은 토/일/공휴일에는 적용되지 않습니다.") arrived
# with strResult=SUCC and a real, cancelable PNR -- a WARNING attached to a
# SUCCESSFUL reservation (docs/MUTATION_HANDOFF.md:181-184, CHANGELOG.md:61-64).
# Because classification never introduces a raise, none of these can become an
# error here. tests/test_error_classification.py pins that.
#
# NOT ENCODED, deliberately:
#   IRT010110  srtgo's second sold-out code (srtgo/srtgo/ktx.py:388) -- 0-hit in
#              jadx, all three smali trees, analysis/raw and analysis/splits.
#   "MACRO"    srtgo_plus's anti-macro substring test (srtgo/srtgo.py:756) -- the
#              app's anti-macro refusal is a DynaPath-Result header, see
#              KorailDynaPathError.
#   S198       the app special-cases it, but ONLY for dao_verify_maas_status
#              (BaseActivity.java:621, ui/menu/BasketTicketActivity.java:811), a
#              MaaS surface this library does not implement. Promoting an
#              endpoint-scoped code to a global rule would misfile it everywhere
#              else.
#   ERT800077  "좌석변경 중 문제가 발생하였습니다. 다시 시도해주세요."
#              (TCSOptionsActivity.java:555) -- the app's own text invites a
#              retry, and this library adds no retry logic, so it stays a plain
#              KorailAppError rather than gaining a class that implies one.
#   "[3]인증정보에 문제가 있습니다."  seen once live on a seat-inventory read after
#              a burst of calls. NO h_msg_cd was captured with it and the string
#              is 0-hit in the APK, so there is nothing to key on; classifying it
#              would mean matching Korean text, which is the practice this map
#              exists to replace. Its trigger is unconfirmed -- plausibly rate
#              limiting, plausibly a DynaPath or session problem. It surfaces as
#              a plain KorailAppError with its message intact; see the taxonomy
#              section of README.md.
# ---------------------------------------------------------------------------

#: Request understood, nothing matched. ``WRG000000``/``P114`` are APK-attested
#: as empty-view states; ``P100``/``WRT300005`` are live-observed only.
NO_RESULT_CODES = frozenset({"WRG000000", "P114", "P100", "WRT300005"})

#: No direct train; the app re-asks the same query as a transfer search.
NO_DIRECT_TRAIN_CODE = "WRD000061"

#: Inventory exhausted. APK-attested; srtgo's ``IRT010110`` is not included.
SOLD_OUT_CODES = frozenset({"ERR211161"})

#: The designated seat cannot be given, but the train may still be bookable.
SEAT_UNAVAILABLE_CODES = frozenset({"WRI411345", "ERR911081", "WRT800176"})

#: Reserve refused; the app routes the user to their existing reservations.
RESERVATION_REFUSED_CODES = frozenset({"WRR800029", "ERR911531", "ERR911051"})

#: Field-level validation replies. Live-observed only; 0-hit in the APK.
INVALID_REQUEST_CODES = frozenset({"WRG200018", "WRT100002", "WRT100124"})

#: The account lacks the entitlement. Live-observed only; 0-hit in the APK.
NOT_ENTITLED_CODES = frozenset({"ERR299943"})

#: Back end declared unavailable; the app offers its offline ticket screen.
SERVICE_UNAVAILABLE_CODE = "SEMGTK"

#: This client version is refused; the app sends the user to Google Play.
APP_UPDATE_REQUIRED_CODE = "SUPDATE"

#: Session expired. Handled before this map, by :class:`KorailSessionExpiredError`.
SESSION_EXPIRED_CODE = "P058"

_APP_ERROR_BY_CODE: dict[str, type[KorailAppError]] = {
    **{code: KorailNoResultsError for code in NO_RESULT_CODES},
    NO_DIRECT_TRAIN_CODE: KorailNoDirectTrainError,
    **{code: KorailSoldOutError for code in SOLD_OUT_CODES},
    **{code: KorailSeatUnavailableError for code in SEAT_UNAVAILABLE_CODES},
    **{
        code: KorailReservationRefusedError
        for code in RESERVATION_REFUSED_CODES
    },
    **{code: KorailInvalidRequestError for code in INVALID_REQUEST_CODES},
    **{code: KorailNotEntitledError for code in NOT_ENTITLED_CODES},
    SERVICE_UNAVAILABLE_CODE: KorailServiceUnavailableError,
    APP_UPDATE_REQUIRED_CODE: KorailAppUpdateRequiredError,
}


def classify_app_error(
    code: str | None,
    message: str | None,
    *,
    raw: object | None = None,
) -> KorailAppError:
    """Build the most specific :class:`KorailAppError` the ``h_msg_cd`` justifies.

    Returns rather than raises, so each call site keeps its own ``raise`` and its
    own traceback. An unknown or absent code yields a plain
    :class:`KorailAppError` — the pre-existing behaviour, unchanged — and every
    result carries ``code``/``message``/``raw`` exactly as before, so a caller
    can migrate incrementally and so the map above can be grown from real
    traffic.

    This function decides only WHICH exception describes a failure, never
    WHETHER there is one. Call it where a :class:`KorailAppError` was already
    about to be raised; passing it a successful response's code would invent a
    failure the server did not report.

    ``P058`` is not handled here: it is answered by
    :class:`KorailSessionExpiredError`, which is a :class:`KorailAuthError` and
    not a :class:`KorailAppError`, and is raised before this map is consulted.
    """
    subclass = _APP_ERROR_BY_CODE.get(code or "", KorailAppError)
    return subclass(code, message, raw=raw)
