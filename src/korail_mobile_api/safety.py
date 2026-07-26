from collections.abc import Mapping, Sequence
import re
from typing import Any
from urllib.parse import urlsplit

from .constants import (
    KORAIL_BASE_URL,
    KORAIL_NETFUNNEL_PATH,
    KORAIL_NETFUNNEL_SERVICE_ID,
    KORAIL_NETFUNNEL_URL,
    KorailNetFunnelAction,
    KorailNetFunnelOpcode,
)
from .errors import KorailProtocolError


# The subject areas this package will not build a send path for.
#
# NARROWED ON 2026-07-26: the label was "points-mileage", which excluded the
# whole loyalty area including its balance READS. Those reads are now in scope
# and two of them are implemented (xPoint.MyXPointView, mlg.amtSpec.do), so the
# label is now "points-mileage-write" and names only what it still refuses:
# anything that moves, earns, spends or re-authenticates points.
#
# Concretely still out, and each for a stated reason rather than by category:
#
#   mlg.lpotAthn.do     -- authenticates against L.POINT with a user-supplied
#                          numeric password and returns pwdErrTno, a FAILURE
#                          COUNTER. A wrong guess is a state change at the
#                          loyalty provider and repeated guesses lock the
#                          account, so this is not a read regardless of the
#                          Korean word 조회 in its screen title.
#   xPoint.XPointView   -- same shape, same objection (xpoint_no + xpoint_pwd).
#   xPoint.OkCashbagCertView, mileage.acpnMlgSave.do, mileage.acpnMlgNoti.do
#                       -- registration/accrual writes.
#
# This set is documentary: nothing dispatches on it, and the actual boundary is
# KORAIL_READ_ONLY_ROUTES plus KORAIL_MUTATION_ROUTES. It is kept because it
# records which areas were considered and declined, which a route allowlist
# cannot express.
EXCLUDED_API_DOMAINS = frozenset(
    {
        "reservation",
        "payment",
        "refund",
        "check-in",
        "member-drop",
        "push-sms",
        "points-mileage-write",
        "dynapath-token-generation",
    }
)

# The exact (method, path) pairs the read-only send path will transmit to.
#
# 58 entries, 58 distinct paths, pinned by tests. The count is not 52 because
# two of the entries are session routes rather than reads: the login POST and
# the server-side logout GET (cookie-authenticated, zero parameters, not a
# mutation), which was added later than the other 50. There is no "excluding
# logout" counting convention — docs that said 50 were simply stale.
#
# NOTE on certification.ReservationList: that path carries TWO Retrofit
# overloads in the app. Only the read one (`inquiryTicketRsv`,
# CertificationService.java:45-46, four query fields) is registered here; the
# write-flavoured `applyDisabilityCertification` (:22) shares the path but adds
# txtPsgDisc0019Cnt plus six @QueryMaps. KORAIL_EXACT_REQUEST_FIELDS pins the
# read overload's exact four fields, so the write overload's shape can never be
# emitted through this route.
KORAIL_READ_ONLY_ROUTES = frozenset(
    {
        ("GET", "/file/CACHE/MobileService.cache"),
        ("GET", "/file/CACHE/prdMobilePlusMain.cache"),
        ("GET", "/file/CACHE/prdMobilePlusNotice.cache"),
        ("POST", "/classes/com.korail.mobile.common.code.do"),
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("GET", "/classes/com.korail.mobile.login.Logout"),
        ("GET", "/classes/com.korail.mobile.common.stationinfo"),
        ("GET", "/classes/com.korail.mobile.common.stationdata"),
        ("GET", "/classes/com.korail.mobile.schedule.runDt"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleView"),
        (
            "POST",
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
        ),
        ("POST", "/classes/com.korail.mobile.qry.chtnStn.do"),
        ("POST", "/classes/com.korail.mobile.myTicket.MyTicketList"),
        ("GET", "/ebizcross/getUUID.do"),
        ("POST", "/classes/com.korail.mobile.copt.gdMenuLt.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do"),
        ("POST", "/classes/com.korail.mobile.cart.showCartList"),
        ("POST", "/classes/com.korail.mobile.dlay.dptnBank.do"),
        (
            "POST",
            "/classes/com.korail.mobile.passCard.DelayDiscountView",
        ),
        ("POST", "/classes/com.korail.mobile.passCard.CouponView"),
        ("POST", "/classes/com.korail.mobile.pass.passInfoList"),
        (
            "POST",
            "/classes/com.korail.mobile.pass.passScheduleInfoList",
        ),
        ("POST", "/classes/com.korail.mobile.pass.trGdMenuLt.do"),
        ("POST", "/classes/com.korail.mobile.pass.passMenu.do"),
        ("GET", "/classes/com.korail.mobile.push.crwCallRq.do"),
        ("GET", "/classes/com.korail.mobile.push.cmtrKnd.do"),
        ("GET", "/classes/com.korail.mobile.product.ReservationList"),
        ("GET", "/classes/com.korail.mobile.product.ReservationDetail"),
        ("POST", "/classes/com.korail.mobile.receipt.ReceiptInfo"),
        (
            "GET",
            "/classes/com.korail.mobile.reservation.ReservationView",
        ),
        ("POST", "/classes/com.korail.mobile.research.TrainResearch"),
        (
            "POST",
            "/classes/com.korail.mobile.research.TResidualSeatsResearch.do",
        ),
        ("POST", "/classes/com.korail.mobile.trn.fresScar.do"),
        (
            "POST",
            "/classes/com.korail.mobile.reservation.guideSeatCnd.do",
        ),
        (
            "POST",
            "/classes/com.korail.mobile.research.assignScheduleView.do",
        ),
        (
            "POST",
            "/classes/com.korail.mobile.research.mergeSeatsC.do",
        ),
        ("POST", "/classes/com.korail.mobile.lmu.scdlQry.do"),
        (
            "POST",
            "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do",
        ),
        (
            "POST",
            "/classes/com.korail.mobile.seatMovie.LimousineScheduleView",
        ),
        ("POST", "/classes/com.korail.mobile.cust.mchdDcntTgt.do"),
        ("POST", "/classes/com.korail.mobile.research.custTripInfo.do"),
        ("POST", "/classes/com.korail.mobile.copt.gdReqQry.do"),
        ("POST", "/classes/com.korail.mobile.reservation.tripChgDate.do"),
        ("POST", "/classes/com.korail.mobile.gift.gdLst.do"),
        ("POST", "/classes/com.korail.mobile.research.cmtrInfo.do"),
        ("POST", "/classes/com.korail.mobile.trn.prcFare.do"),
        ("POST", "/classes/com.korail.mobile.tk.dlvRcvCust.do"),
        (
            "POST",
            "/classes/com.korail.mobile.ticket.ticketDupCheck.do",
        ),
        ("POST", "/classes/com.korail.mobile.tk.pbpAcepSpec.do"),
        ("POST", "/classes/com.korail.mobile.tk.plfNo.do"),
        ("POST", "/classes/com.korail.mobile.tk.rcntDlvHst.do"),
        (
            "GET",
            "/classes/com.korail.mobile.certification.ReservationList",
        ),
        ("POST", "/classes/com.korail.mobile.refunds.CommissionView"),
        ("POST", "/classes/com.korail.mobile.refunds.SelTicketInfo"),
        # Loyalty READS. Neither carries a password and neither moves a point:
        # MyXPointView is the my-page summary the app fetches on open
        # (MyPageActivity.java:414) with point_dv_cd pinned to "0" by the DAO
        # itself (KorailPointInquiryDao.java:91), and mlg.amtSpec.do is the
        # 적립/사용 history list. The password-bearing loyalty routes
        # (mlg.lpotAthn.do, xPoint.XPointView) are excluded -- see
        # EXCLUDED_API_DOMAINS above.
        ("POST", "/classes/com.korail.mobile.xPoint.MyXPointView"),
        ("POST", "/classes/com.korail.mobile.mlg.amtSpec.do"),
        # 할인카드(N카드) reads. Both are GETs whose only credential is the
        # session cookie, and neither changes anything: one lists the trips a
        # card has already been spent on, the other lists the trains a card
        # may still be spent on. The two dcntCrd* routes that DO change state
        # (research.dcntCrdInfo.do, reservation.dcntCrdExtn.do) are
        # deliberately absent from this set.
        ("GET", "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do"),
        (
            "GET",
            "/classes/com.korail.mobile.research.dcntCrdScheduleView.do",
        ),
    }
)

# Tiering of the state-changing routes. These are the four core mutation
# endpoints (one per category) plus the 예약대기 follow-up, which shares the
# "reserve" category with the hold it completes. They are deliberately kept OUT
# of KORAIL_READ_ONLY_ROUTES so the read-only allowlist and its guarantee remain
# fully intact: the read-only send path (post_form/get_json) refuses every route
# in this set.
#
# This is NOT an inert classification. All four categories now have a callable
# client method — KorailClient.reserve, .confirm_standby_hold,
# .cancel_unpaid_hold, .pay_with_fake_card and .refund — and each of them CAN
# transmit to its route below. What bounds
# them is the gate, not the absence of a method: the only code that sends to a
# route in this set is KorailHttpClient.post_mutation_form, which requires a
# MutationConsent opting into the matching category, refuses a dry_run=True
# consent, refuses a payment unless fake_card_only is set, and re-checks both
# assert_mutation_route and assert_mutation_route_category before the POST.
# Under the default consent (dry_run=True) the methods build a redacted preview
# and send nothing.
#
# Each tuple is (HTTP method, exact relative path); the trailing comment names
# the consent category that owns the route.
KORAIL_MUTATION_ROUTES = frozenset(
    {
        # reserve
        ("POST", "/classes/com.korail.mobile.certification.TicketReservation"),
        # reserve -- the 예약대기 follow-up. Deliberately the SAME category as
        # the hold that creates it, not a new one. It changes no money and
        # releases no seat; it records the two options
        # (좌석등급 변경 / SMS 통보) that the standby screen collects for a PNR
        # the caller has just created with an allow_reserve consent
        # (ReservationWaitService.java:10-12, reached only from
        # ui/inquiry/rir/orr/a.java:222-225 after a "1102" hold). Splitting it
        # into its own category would mean a caller who opted into placing a
        # standby booking could not finish placing it, which is not a safety
        # boundary -- and every existing MutationConsent would silently deny an
        # operation it plainly intended to allow. The route/category cross-check
        # below still stops a reserve consent from reaching payment, cancel or
        # refund.
        ("POST", "/classes/com.korail.mobile.reservationWait.ReservationWait"),
        # payment
        ("POST", "/classes/com.korail.mobile.payment.ReservationPayment"),
        # cancel
        (
            "POST",
            "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk",
        ),
        # refund
        ("POST", "/classes/com.korail.mobile.refunds.RefundsRequest"),
    }
)

# The consent category each mutation route belongs to. The mutation send path
# cross-checks the caller-supplied category against the route so a consent for
# one category (e.g. "reserve") can never be used to POST a different category's
# route (e.g. the refund route).
KORAIL_MUTATION_ROUTE_CATEGORIES = {
    "/classes/com.korail.mobile.certification.TicketReservation": "reserve",
    "/classes/com.korail.mobile.reservationWait.ReservationWait": "reserve",
    "/classes/com.korail.mobile.payment.ReservationPayment": "payment",
    "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk": (
        "cancel"
    ),
    "/classes/com.korail.mobile.refunds.RefundsRequest": "refund",
}


def assert_mutation_route_category(path: str, category: str) -> None:
    """Ensure ``category`` is the one that owns mutation route ``path``.

    Raises :class:`KorailProtocolError` when the path is not a known mutation
    route or when the caller's category does not match the route's category, so
    a per-category consent cannot be redirected to a different category's route.
    """
    parsed_path = urlsplit(path).path
    expected = KORAIL_MUTATION_ROUTE_CATEGORIES.get(parsed_path)
    if expected is None:
        raise KorailProtocolError(
            f"KORAIL mutation route is not allowed: POST {parsed_path}"
        )
    if category != expected:
        raise KorailProtocolError(
            f"KORAIL mutation category {category!r} does not match route "
            f"{parsed_path} (expected {expected!r})"
        )

KORAIL_HTTPS_HOST = urlsplit(KORAIL_BASE_URL).hostname
KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

# ---------------------------------------------------------------------------
# The NetFunnel queue protocol: one exact query contract per opcode.
#
# THREE NAMED CONTRACTS, NOT ONE LOOSENED ONE. The queue lives on a different
# host from every other route in this module, so it could not simply be added to
# KORAIL_READ_ONLY_ROUTES — and it deliberately was not, because that set is the
# app-origin allowlist and post_form/get_json must never be able to target
# ts.wseq. What is registered instead is the exact parameter list of each opcode
# this library issues, IN ORDER, so adding a queue operation means registering
# it rather than relaxing a check.
#
# Every tuple below is the sequence of `U6.a.addParam` calls in the matching
# T6/d.java builder. U6/a.java:57-63 appends each one to an ArrayList and
# U6/a.java:180-185 renders that list with URLEncodedUtils.format, so the app's
# call order IS the wire order:
#
#   5101 GetTidCacekedEnter  (T6/d.java:99-101)   opcode, sid, aid
#   5002 CheckedEnter        (T6/d.java:54-55)    opcode, key
#   5004 Complete            (T6/d.java:78-79)    opcode, key
#
# Note what is absent, because it is what a reader coming from the SRT sibling
# will expect to find: no `js`, no `nfid`, no `prefix`, no trailing epoch
# millisecond, and no `ttl` anywhere. Those belong to the JavaScript NetFunnel
# client that SRT's WebView loads. KORAIL embeds the native Android SDK instead,
# and the native SDK sends none of them — see the module docstring of
# korail_mobile_api.netfunnel. `js=yes` in particular is a real parameter of the
# other dialect (srtgo and ryanking13 both spell it `js=true`, which is wrong
# there too) and simply has no place here.
#
# 5003 ALIVE_NOTICE, 5105 INIT and 5106 STOP are NOT registered. The first keeps
# a waiting-room popup alive that this library never renders; the other two are
# administrative and the app's own SDK refuses them without touching the network
# (T6/d.java:115-121). An unregistered opcode is rejected by
# assert_netfunnel_request, which is the point of registering rather than
# pattern-matching.
# ---------------------------------------------------------------------------
KORAIL_NETFUNNEL_ROUTES = frozenset({("GET", KORAIL_NETFUNNEL_PATH)})

KORAIL_NETFUNNEL_QUERY_CONTRACTS: dict[str, tuple[str, ...]] = {
    KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value: ("opcode", "sid", "aid"),
    KorailNetFunnelOpcode.CHK_ENTER.value: ("opcode", "key"),
    KorailNetFunnelOpcode.SET_COMPLETE.value: ("opcode", "key"),
}

#: Opcodes whose request carries the slot key. Kept as data beside the contracts
#: so "which opcode has which field" is answerable by reading, not by tracing.
KORAIL_NETFUNNEL_KEYED_OPCODES = frozenset(
    {
        KorailNetFunnelOpcode.CHK_ENTER.value,
        KorailNetFunnelOpcode.SET_COMPLETE.value,
    }
)

#: The only action ids that may appear in an ``aid``. All eight the app declares
#: (``K4/g.java:43-51``) — including the two it never calls — and nothing else,
#: so ``aid`` cannot become a free-text field a bug smuggles a value through.
KORAIL_NETFUNNEL_ACTION_IDS = frozenset(
    action.value for action in KorailNetFunnelAction
)

# The key is opaque and server-issued, so it is validated by SHAPE: a non-empty
# run of the characters a NetFunnel key is made of.
#
# THE 512 BOUND IS A CEILING TAKEN FROM A SCAR, NOT A GUESS. The sibling SRT
# implementation bounded the same field at 128 while real keys are 256 characters
# of uppercase hex. Every setComplete therefore failed this check before it was
# sent, and because a failed release was swallowed there, it failed SILENTLY —
# every slot leaked until a live run exposed it. Nothing offline could have
# caught it, which is exactly why the bound here is generous and why
# KorailNetFunnelClient.release raises instead of swallowing.
KORAIL_NETFUNNEL_KEY_RE = re.compile(r"[A-Za-z0-9_.:@~-]{1,512}")

# ---------------------------------------------------------------------------
# THE QUEUE IS A POOL OF NODES, AND FOLLOWING ONE IS NOT OPTIONAL.
#
# `nf.letskorail.com` is a FRONT DOOR. It load-balances the entry call across a
# pool of queue nodes, and the node that issues a session is the only one that
# can complete it. Every reply names the node that answered it, in its `ip` and
# `port` fields (`T6/i.java:50-53` reads them into the response object's host and
# port), and the app follows that naming: `T6/d.java:17-19` (`makeURL`) rebuilds
# the URL from `iVar.getHost()`/`iVar.getPort()` for `chkEnter`, `aliveNotice`
# and `setComplete` unless `host_notmodify` is set — and `host_notmodify` is
# false by default (`T6/h.java:43`, `isHostNotmodify()` at :134-135) and
# `KTApplication` never sets it. Only the entry call, which has no previous
# reply to name a node, goes to the configured host.
#
# DIAGNOSED LIVE ON 2026-07-26, and the symptom was not obvious. This module used
# to decline the redirection and send every opcode to the front door. Slot
# release then failed ABOUT HALF THE TIME, non-deterministically — five
# acquire-then-release cycles, all entered through `nf.letskorail.com`:
#
#     acquire said ip=rnf12.letskorail.com  -> release 503
#     acquire said ip=rnf12.letskorail.com  -> release 503
#     acquire said ip=rnf13.letskorail.com  -> release 503
#     acquire said ip=rnf14.letskorail.com  -> release 200
#     acquire said ip=rnf13.letskorail.com  -> release 200
#
# and the controlled pair that names the cause outright:
#
#     acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
#       release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
#       release via rnf13.letskorail.com -> 200:key=&nwait=0&...
#
# `Wrong Server ID` IS LITERAL. It is the pool saying "that session is not
# mine" — not a complaint about a credential, a parameter or a key generation.
# The releases that succeeded were the balancer happening to land the
# front-door request back on the node that owned the session. The price of
# staying pinned was leaking roughly half of every queue slot we took, which is
# precisely the behaviour NetFunnel exists to prevent.
#
# CONSTRAINED, NOT TRUSTED. A response choosing where the next request goes is
# exactly what an origin guard exists to stop, so the redirection is admitted
# only into the queue's OWN node naming, and a reply naming anything else is a
# hard error rather than a quiet fall-back to the front door. Falling back
# silently is what produced the flaky release in the first place: it turns "this
# reply is lying to us" into "this slot leaked", which is unobservable.
#
# THE RULE, and why it is drawn where it is. The observed nodes are
# `rnf12`, `rnf13` and `rnf14`, all under `letskorail.com`, all https on 443. So:
#
#   * the label is `rnf` followed by a decimal 1..99 with NO leading zero — the
#     observed names are contiguous small integers, so the shape is "the pool's
#     n-th node" and two digits already admits 99 of them. A leading zero is
#     refused because `rnf013` is not a name the pool hands out and a
#     normalisation question is not worth inviting into a guard.
#   * the parent is EXACTLY `letskorail.com`, matched as whole labels, so
#     `rnf13.letskorail.com.example.net` and `evil-rnf13.letskorail.com` are not
#     nodes.
#   * lowercase, exactly as the wire spells it. DNS would not care; a guard
#     comparing raw response bytes should, and refusing the case variants we have
#     never seen costs nothing.
#   * https on port 443 and nothing else — the port is NOT followed blindly
#     either. 443 is the only value observed and the only one the front-door
#     guard permits, so any other is refused.
#   * plus the front door itself, which is already the pinned origin: a reply
#     naming `nf.letskorail.com` is the balancer naming itself, and admitting it
#     grants no reach that the client did not already have.
# ---------------------------------------------------------------------------

#: The node label a queue reply may name. See the block comment above for why
#: each part of this is as tight as it is.
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")

#: The only port a named node may be on. Observed as 443 on every reply, and the
#: only port :func:`assert_korail_netfunnel_origin` permits for the front door.
KORAIL_NETFUNNEL_NODE_PORT = 443

#: The opcodes that belong to an ESTABLISHED SESSION and therefore go to the node
#: that issued it. ``5101`` is deliberately absent: the entry call is the one the
#: front door balances, and it has no previous reply to name a node anyway.
#:
#: This coincides with :data:`KORAIL_NETFUNNEL_KEYED_OPCODES` today, and not by
#: accident — a session is identified by its key and lives on its node, so the
#: opcodes that carry one are the opcodes that must reach the other. They stay
#: separate constants because they answer different questions.
KORAIL_NETFUNNEL_NODE_OPCODES = frozenset(
    {
        KorailNetFunnelOpcode.CHK_ENTER.value,
        KorailNetFunnelOpcode.SET_COMPLETE.value,
    }
)


def _assert_netfunnel_origin(netfunnel_url: str, *, allow_nodes: bool) -> None:
    """The structural half of both queue-origin guards.

    Everything except *which hostnames* are acceptable is identical between the
    front door and a queue node — https, no userinfo, no path, no query, no
    fragment, port 443 or implicit — so it is written once and the hostname rule
    is the only parameter.
    """
    parsed = urlsplit(netfunnel_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise KorailProtocolError(
            "KORAIL NetFunnel request origin is not allowed"
        ) from exc
    hostname = (parsed.hostname or "").casefold()
    host_allowed = hostname == KORAIL_NETFUNNEL_HTTPS_HOST or (
        allow_nodes
        and KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(hostname) is not None
    )
    if (
        parsed.scheme.casefold() != "https"
        or parsed.hostname is None
        or not host_allowed
        or port not in {None, KORAIL_NETFUNNEL_NODE_PORT}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise KorailProtocolError(
            "KORAIL NetFunnel request origin is not allowed"
        )


def assert_korail_netfunnel_origin(netfunnel_url: str) -> None:
    """Pin the queue's FRONT DOOR to ``https://nf.letskorail.com`` (port 443).

    The NetFunnel counterpart to :func:`assert_korail_origin`, and deliberately
    a separate function over a separate constant: the API client may not reach
    the queue host and the queue client may not reach the API host.

    This is the guard for the configured origin and for the entry call
    (``5101``), and it admits the front door ONLY — a queue node is refused here.
    The follow-up opcodes have their own, wider guard in
    :func:`assert_korail_netfunnel_node_origin`; see
    :func:`assert_korail_netfunnel_opcode_origin` for which is which.
    """
    _assert_netfunnel_origin(netfunnel_url, allow_nodes=False)


def assert_korail_netfunnel_node_origin(netfunnel_url: str) -> None:
    """Pin a session's origin to the front door or one of the queue's own nodes.

    Admits ``https://nf.letskorail.com`` and ``https://rnf<N>.letskorail.com``
    on port 443, and nothing else. See the block comment above
    :data:`KORAIL_NETFUNNEL_NODE_HOST_RE` for the live evidence that the pool is
    real and for why the rule is drawn exactly here.
    """
    _assert_netfunnel_origin(netfunnel_url, allow_nodes=True)


def assert_korail_netfunnel_opcode_origin(
    opcode: str,
    netfunnel_url: str,
) -> None:
    """Which host this opcode is allowed to be sent to.

    ``5101`` getTidChkEnter is the entry call and goes to the FRONT DOOR, which
    is what balances it across the pool. ``5002`` chkEnter and ``5004``
    setComplete belong to a session and go to the NODE that issued it — the
    front door does not own that session and answers
    ``503:msg="Wrong Server ID"`` when it is asked to complete it.

    The split lives here rather than in the client so that "which host does this
    opcode go to" is answered by the guard, not by whichever call site happened
    to build the URL.
    """
    if opcode in KORAIL_NETFUNNEL_NODE_OPCODES:
        assert_korail_netfunnel_node_origin(netfunnel_url)
    else:
        assert_korail_netfunnel_origin(netfunnel_url)


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """Turn a reply's ``ip``/``port`` into the origin of the node that answered.

    Returns the origin URL (``https://<host>``), or ``""`` when the reply named
    no node at all — which is the ``getHost().length() <= 0 || getPort() <= 0``
    branch of ``T6/d.makeURL`` (``T6/d.java:17-19``), and is the ONLY case in
    which a follow-up legitimately goes to the front door. ``ip`` and ``port``
    travel together on every reply that has ever been seen, so naming one
    without the other is treated as naming a node badly, not as naming none.

    Raises :class:`KorailProtocolError` for a host outside the queue's own node
    naming and for any port but 443. That refusal is deliberately LOUD: silently
    falling back to the front door here is the defect this function was added to
    fix, because it converts a bad redirection into a leaked queue slot, and a
    leaked slot makes no noise at all.
    """
    if not ip and not port:
        return ""
    if (
        ip != KORAIL_NETFUNNEL_HTTPS_HOST
        and KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(ip) is None
    ):
        raise KorailProtocolError(
            f"KORAIL NetFunnel reply named {ip!r} as the host for the rest of "
            "this session, and it is not one of the queue's own nodes "
            "(rnf<1-99>.letskorail.com, lowercase) nor the front door "
            f"{KORAIL_NETFUNNEL_HTTPS_HOST!r}; the redirection this queue needs "
            "is constrained to the pool, never trusted as given"
        )
    if port != str(KORAIL_NETFUNNEL_NODE_PORT):
        raise KorailProtocolError(
            f"KORAIL NetFunnel reply named port {port!r} for queue node {ip!r}; "
            f"only {KORAIL_NETFUNNEL_NODE_PORT} is allowed, and the port is no "
            "more followed on the server's say-so than the host is"
        )
    return f"https://{ip}"


def assert_netfunnel_request(
    method: str,
    path: str,
    params: Sequence[tuple[str, str]],
) -> None:
    """Allow only a registered queue opcode, with its exact ordered parameters.

    ``params`` is checked as the ordered name/value pairs the request will be
    built from, before encoding, so the contract covers the parameter ORDER as
    well as its membership — the app's order is not decorative, it is simply
    what ``URLEncodedUtils.format`` emits from the list ``T6/d.java`` built.

    Raises :class:`KorailProtocolError` for an unregistered opcode (5003, 5105,
    5106 and anything invented), for a parameter list that is not exactly the
    contract in exactly that order, for a ``sid`` that is not ``service_1``, for
    an ``aid`` outside :data:`KORAIL_NETFUNNEL_ACTION_IDS`, and for a key that is
    not the shape a NetFunnel key has.
    """
    route = (method.upper(), urlsplit(path).path)
    if route not in KORAIL_NETFUNNEL_ROUTES:
        raise KorailProtocolError(
            f"KORAIL NetFunnel route is not allowed: {route[0]} {route[1]}"
        )
    pairs = tuple(params)
    if any(
        type(pair) is not tuple
        or len(pair) != 2
        or not isinstance(pair[0], str)
        or not isinstance(pair[1], str)
        for pair in pairs
    ):
        raise KorailProtocolError(
            "KORAIL NetFunnel parameters must be ordered string pairs"
        )
    values = dict(pairs)
    opcode = values.get("opcode", "")
    contract = KORAIL_NETFUNNEL_QUERY_CONTRACTS.get(opcode)
    if contract is None:
        raise KorailProtocolError(
            f"KORAIL NetFunnel opcode {opcode!r} is not one of the registered "
            "queue operations (5101 getTidChkEnter, 5002 chkEnter, "
            "5004 setComplete)"
        )
    if tuple(name for name, _value in pairs) != contract:
        raise KorailProtocolError(
            f"KORAIL NetFunnel request is not the registered opcode-{opcode} "
            "contract: expected exactly " + ", ".join(contract) + " in order"
        )
    if opcode in KORAIL_NETFUNNEL_KEYED_OPCODES and (
        KORAIL_NETFUNNEL_KEY_RE.fullmatch(values["key"]) is None
    ):
        raise KorailProtocolError(
            "KORAIL NetFunnel key parameter is missing or malformed"
        )
    if "sid" in values and values["sid"] != KORAIL_NETFUNNEL_SERVICE_ID:
        raise KorailProtocolError(
            "KORAIL NetFunnel service id must be "
            f"{KORAIL_NETFUNNEL_SERVICE_ID!r}"
        )
    if "aid" in values and values["aid"] not in KORAIL_NETFUNNEL_ACTION_IDS:
        raise KorailProtocolError(
            f"KORAIL NetFunnel action id {values['aid']!r} is not one the app "
            "declares"
        )


KORAIL_EXACT_REQUEST_FIELDS = {
    "/file/CACHE/MobileService.cache": frozenset({"timeStamp"}),
    "/classes/com.korail.mobile.login.Logout": frozenset(),
    "/classes/com.korail.mobile.cart.showCartList": frozenset(
        {"Device", "Version", "Key", "pnrNo", "addSrvReqNo"}
    ),
    "/classes/com.korail.mobile.dlay.dptnBank.do": frozenset(
        {"Device", "Version", "Key"}
    ),
    "/classes/com.korail.mobile.passCard.DelayDiscountView": frozenset(
        {"Device", "Version", "Key", "dptDtTo"}
    ),
    "/classes/com.korail.mobile.passCard.CouponView": frozenset(
        {"Device", "Version", "Key", "txtSelPage", "pnrNo"}
    ),
    "/classes/com.korail.mobile.pass.passInfoList": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "txtCmtrKndCd",
            "txtCmtrUtlTrmCd",
            "txtCmtrUtlAgeCd",
        }
    ),
    "/classes/com.korail.mobile.pass.passScheduleInfoList": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "selGoTrain",
            "selGoAbrdDt",
            "txtGoHour",
            "radChgTrnDvCd",
            "txtCmtrKndCd",
            "txtCmtrUtlTrmCd",
            "txtCmtrUtlAgeCd",
            "txtSelPage",
            "txtCntPerPage",
            "txtGoStart",
            "txtGoEnd",
            "txtWkndUseFlg",
        }
    ),
    "/classes/com.korail.mobile.pass.trGdMenuLt.do": frozenset(
        {"Device", "Version"}
    ),
    "/classes/com.korail.mobile.pass.passMenu.do": frozenset(
        {"Device", "Version", "Key", "menuNo"}
    ),
    "/classes/com.korail.mobile.push.crwCallRq.do": frozenset(
        {"Device", "Version", "Key", "qryDvCd"}
    ),
    "/classes/com.korail.mobile.push.cmtrKnd.do": frozenset(
        {"Device", "Version", "Key", "cmtrKndCd"}
    ),
    "/classes/com.korail.mobile.product.ReservationList": frozenset(
        {"Device", "Version", "Key", "txtSelPage", "txtCntPerPage"}
    ),
    "/classes/com.korail.mobile.product.ReservationDetail": frozenset(
        {"Device", "Version", "Key", "txtVrRsNo", "txtVrRsvSqNo"}
    ),
    "/classes/com.korail.mobile.receipt.ReceiptInfo": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "h_orgtk_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_tk_ret_pwd",
        }
    ),
    "/classes/com.korail.mobile.reservation.ReservationView": frozenset(
        {"Device", "Version", "Key"}
    ),
    "/classes/com.korail.mobile.copt.gdMenuLt.do": frozenset(
        {"Device", "Version"}
    ),
    "/classes/com.korail.mobile.research.TrainResearch": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "Sid",
            "txtMenuId",
            "txtPsrmClCd",
            "txtRunDt",
            "txtDptDt",
            "txtTrnClsfCd",
            "txtTrnNo",
            "txtDptRsStnCd",
            "txtArvRsStnCd",
            "txtDptStnRunOrdr",
            "txtArvStnRunOrdr",
            "txtTrnGpCd",
            "txtTotPsgCnt",
            "txtSeatAttCd",
            "txtGdNo",
        }
    ),
    "/classes/com.korail.mobile.research.TResidualSeatsResearch.do": (
        frozenset(
            {
                "Device",
                "Version",
                "Key",
                "trnClsfCd",
                "trnGpCd",
                "runDt",
                "trnNo",
                "srcarNo",
                "psrmClCd",
                "dptRsStnCd",
                "arvRsStnCd",
                "seatAttCd",
                "dptStnRunOrdr",
                "arvStnRunOrdr",
                "totPsgCnt",
                "gdNo",
                "isArrow",
                "Sid",
                "ctlDvCd",
            }
        )
    ),
    "/classes/com.korail.mobile.trn.fresScar.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "runDt",
            "trnNo",
            "dptStnConsOrdr",
            "arvStnConsOrdr",
            "dptStnRunOrdr",
            "arvStnRunOrdr",
        }
    ),
    "/classes/com.korail.mobile.reservation.guideSeatCnd.do": (
        frozenset({"Device", "Version", "Key", "rqSeatAttCd"})
    ),
    "/classes/com.korail.mobile.research.assignScheduleView.do": (
        frozenset(
            {
                "Device",
                "Version",
                "Key",
                "menuId",
                "dptDt",
                "dptTm",
                "dptRsStnNm",
                "arvRsStnNm",
                "trnGpCd",
                "psrmClCd",
                "seatAttCd1",
                "psgNum1",
                "stlbDturDvNm1",
                "dirtChtnDvCd",
                "chtnArvRsStnNm",
            }
        )
    ),
    "/classes/com.korail.mobile.research.mergeSeatsC.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "abrdDt",
            "runDt",
            "trnNo",
            "dptRsStnNm",
            "arvRsStnNm",
            "selRsStnNm",
            "psrmClCd",
            "seatAttCd",
            "totPsgNum",
        }
    ),
    "/classes/com.korail.mobile.lmu.scdlQry.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "dptDt",
            "dptRsStnCd",
            "arvRsStnCd",
            "tmGpCd",
            "psrmClCd",
            "dptTm",
            "trnNo",
            "seatAttCd",
            "rsvSaleDvCd",
        }
    ),
    "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "trnClsfCd",
            "trnGpCd",
            "runDt",
            "trnNo",
            "srcarNo",
            "psrmClCd",
            "dptRsStnCd",
            "arvRsStnCd",
            "seatAttCd",
            "dptStnRunOrdr",
            "arvStnRunOrdr",
            "totPsgCnt",
            "gdNo",
            "isArrow",
        }
    ),
    "/classes/com.korail.mobile.seatMovie.LimousineScheduleView": (
        frozenset(
            {
                "Device",
                "Version",
                "Sid",
                "txtMenuId",
                "radJobId",
                "txtJobDv",
                "selGoTrain",
                "txtTrnGpCd",
                "txtGoTrnNo",
                "txtGoStart",
                "txtGoEnd",
                "txtGoAbrdDt",
                "txtGoHour",
                "txtPsgFlg_1",
                "txtPsgFlg_2",
                "txtPsgFlg_3",
                "txtPsgFlg_4",
                "txtPsgFlg_5",
                "txtSeatAttCd_2",
                "txtSeatAttCd_3",
                "txtSeatAttCd_4",
                "ebizCrossCheck",
                "srtCheckYn",
                "rtYn",
            }
        )
    ),
    "/classes/com.korail.mobile.cust.mchdDcntTgt.do": frozenset(
        {"Device", "Version", "Key", "dptDt"}
    ),
    "/classes/com.korail.mobile.research.custTripInfo.do": frozenset(
        {"Device", "Version", "Key", "custMgNo", "medDvCd", "regSqno"}
    ),
    "/classes/com.korail.mobile.copt.gdReqQry.do": frozenset(
        {"Device", "Version", "qryDtFrom", "qryDtTo"}
    ),
    "/classes/com.korail.mobile.reservation.tripChgDate.do": frozenset(
        {"Device", "Version", "Key", "tripChgDate"}
    ),
    "/classes/com.korail.mobile.gift.gdLst.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "qryDvCd",
            "qryVal",
            "abrdDtFrom",
            "abrdDtTo",
            "usePsbFlg",
        }
    ),
    "/classes/com.korail.mobile.research.cmtrInfo.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "jobDvCd",
            "cmtrKndCd",
            "psgCnt",
            "cmtrUtlAgeCd",
            "psgPrnb",
            "ogtkSaleWctNo",
            "ogtkSaleDd",
            "ogtkSaleSqno",
            "ogtkRetPwd",
            "inquiryType",
        }
    ),
    "/classes/com.korail.mobile.trn.prcFare.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "txtMenuId",
            "chtnDvCd",
            "dptRsStnCd",
            "arvRsStnCd",
            "runDt",
            "trnNo",
            "gdNo",
            "rqSeatAttCd",
            "trnGpCd",
            "stlbTrnClsfCd",
        }
    ),
    "/classes/com.korail.mobile.tk.dlvRcvCust.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "saleWctNo",
            "saleDt",
            "saleSqno",
            "tkRetPwd",
        }
    ),
    "/classes/com.korail.mobile.ticket.ticketDupCheck.do": frozenset(
        {"Device", "Version", "Key", "pnrNo"}
    ),
    "/classes/com.korail.mobile.tk.pbpAcepSpec.do": frozenset(
        {"Device", "Version", "Key", "tkCnt", "tkRetNo"}
    ),
    "/classes/com.korail.mobile.tk.plfNo.do": frozenset(
        {"Device", "Version", "Key", "tkCnt", "tkRetNo"}
    ),
    "/classes/com.korail.mobile.tk.rcntDlvHst.do": frozenset(
        {"Device", "Version", "Key", "custMgNo"}
    ),
    # The READ overload only. CertificationService.java declares two methods on
    # this one path: inquiryTicketRsv (:45-46) with exactly these four @Query
    # fields, and applyDisabilityCertification (:22) which adds
    # txtPsgDisc0019Cnt and six @QueryMaps to apply a disability certificate to
    # a held reservation. Pinning the four-field set here means the write
    # overload's shape is rejected by assert_read_only_request_fields before it
    # can reach the wire, even though it shares the path.
    "/classes/com.korail.mobile.certification.ReservationList": frozenset(
        {"Device", "Version", "Key", "hidPnrNo"}
    ),
    "/classes/com.korail.mobile.refunds.CommissionView": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "h_orgtk_ret_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_ret_pwd",
            "h_comp_nm",
            "h_comp_cert_no",
        }
    ),
    # Same six identity fields plus h_purchase_history. srtgo calls this route
    # as a GET and omits h_purchase_history (ktx.py:791-800); the app declares
    # @POST @FormUrlEncoded with the full eight-field set
    # (RefundService.java:23-25) and every call site sets the flag
    # (TicketListActivity.java:926 "N", TicketPurchaseHistoryActivity.java:267
    # "Y"). The app wins.
    "/classes/com.korail.mobile.refunds.SelTicketInfo": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "h_orgtk_ret_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_ret_pwd",
            "h_purchase_history",
        }
    ),
    # 마일리지/포인트 요약 (XPointService.java:18-20). point_dv_cd is not a
    # caller parameter: KorailPointInquiryDao.java:91 passes the literal "0" and
    # the DAO has no request class at all, so there is nothing else it can be.
    "/classes/com.korail.mobile.xPoint.MyXPointView": frozenset(
        {"Device", "Version", "Key", "point_dv_cd"}
    ),
    # 마일리지 적립/사용 내역 (XPointService.java:26-28).
    "/classes/com.korail.mobile.mlg.amtSpec.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "pontTpVal",
            "qryDvVal",
            "qryStDt",
            "qryClsDt",
            "pgPrCnt",
            "nowPgNo",
        }
    ),
    # 할인카드(N카드) 사용이력 (ResearchService.java:51-52). One identifier and
    # nothing else: the card number the ticket detail hands out as
    # dcnt_crd_info.h_dcnt_crd_no (Y4/C0907b.java:303 puts it in the intent
    # extra that TicketNCardHistoryActivity.java:137 reads straight into
    # setDcntCrdNo).
    "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do": frozenset(
        {"Device", "Version", "Key", "dcntCrdNo"}
    ),
    # 할인카드(N카드) 스케줄 조회 (ResearchService.java:54-55). Fourteen
    # @Query parameters, of which two are Retrofit-omittable -- see
    # KORAIL_OPTIONAL_REQUEST_FIELDS below.
    "/classes/com.korail.mobile.research.dcntCrdScheduleView.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "dptDt",
            "dptRsStnNm",
            "arvRsStnNm",
            "dptTm",
            "trnGpCd",
            "dirtChtnDvCd",
            "dcntCrdKndCd",
            "dcntCrdKndMgNo",
            "useTrmDno",
            "usePsbTno",
            "qryPgNo",
        }
    ),
}
KORAIL_EXACT_FORM_FIELDS = KORAIL_EXACT_REQUEST_FIELDS

# Fields the app may legitimately OMIT from an otherwise-exact request. On the
# search-derived seat reads the app forwards trainInfo.getH_seat_att_cd() and
# trainInfo.getTxtGdNo() verbatim (x4/b.java:19,23) and Retrofit drops the
# @Field when it is null (ResearchService getCarList txtSeatAttCd:37/txtGdNo:37
# / getSeatList seatAttCd:59/gdNo:59), so a request without the seat-attribute
# code or goods number is contract-conformant. Every other field stays
# required, and no field outside the exact set is ever accepted.
KORAIL_OPTIONAL_REQUEST_FIELDS: dict[str, frozenset[str]] = {
    "/classes/com.korail.mobile.research.TrainResearch": frozenset(
        {"txtSeatAttCd", "txtGdNo"}
    ),
    "/classes/com.korail.mobile.research.TResidualSeatsResearch.do": (
        frozenset({"seatAttCd", "gdNo"})
    ),
    # The N-card schedule view's two never-set @Query parameters. NEITHER of
    # the app's two builders (u4/b.java:52-65 and :67-81) ever calls
    # setQryPgNo, so qryPgNo is always null and Retrofit drops it; and the
    # 1-section builder (:52-65) additionally never calls setUseTrmDno, so a
    # card bought by trip count rather than by period omits that one too. Both
    # are registered as omittable rather than pinned, because a request that
    # includes them is equally contract-conformant -- the response's
    # fllwPgExt/qryPgNo pair is how the app's other paged reads continue, and
    # this route declares the parameter even though v6.5.0 never fills it.
    "/classes/com.korail.mobile.research.dcntCrdScheduleView.do": frozenset(
        {"useTrmDno", "qryPgNo"}
    ),
}

KORAIL_EXACT_REQUEST_FIELD_ORDERS = {
    "/classes/com.korail.mobile.cust.mchdDcntTgt.do": (
        ("Device", "Version", "Key", "dptDt"),
    ),
    "/classes/com.korail.mobile.research.custTripInfo.do": (
        ("Device", "Version", "Key", "custMgNo", "medDvCd", "regSqno"),
    ),
    "/classes/com.korail.mobile.copt.gdReqQry.do": (
        ("Device", "Version"),
        ("Device", "Version", "qryDtFrom", "qryDtTo"),
    ),
    "/classes/com.korail.mobile.reservation.tripChgDate.do": (
        ("Device", "Version", "Key", "tripChgDate"),
    ),
    "/classes/com.korail.mobile.gift.gdLst.do": (
        (
            "Device",
            "Version",
            "Key",
            "qryDvCd",
            "qryVal",
            "abrdDtFrom",
            "abrdDtTo",
            "usePsbFlg",
        ),
        ("Device", "Version", "Key", "qryDvCd", "qryVal"),
    ),
    "/classes/com.korail.mobile.research.cmtrInfo.do": (
        (
            "Device",
            "Version",
            "Key",
            "jobDvCd",
            "cmtrKndCd",
            "psgCnt",
        ),
        (
            "Device",
            "Version",
            "Key",
            "jobDvCd",
            "psgCnt",
            "ogtkSaleWctNo",
            "ogtkSaleDd",
            "ogtkSaleSqno",
            "ogtkRetPwd",
            "inquiryType",
        ),
    ),
    "/classes/com.korail.mobile.trn.prcFare.do": (
        (
            "Device",
            "Version",
            "Key",
            "txtMenuId",
            "chtnDvCd",
            "dptRsStnCd",
            "arvRsStnCd",
            "runDt",
            "trnNo",
            "gdNo",
            "rqSeatAttCd",
            "trnGpCd",
            "stlbTrnClsfCd",
        ),
    ),
    "/classes/com.korail.mobile.tk.dlvRcvCust.do": (
        (
            "Device",
            "Version",
            "Key",
            "saleWctNo",
            "saleDt",
            "saleSqno",
            "tkRetPwd",
        ),
    ),
    "/classes/com.korail.mobile.ticket.ticketDupCheck.do": (
        ("Device", "Version", "Key", "pnrNo"),
    ),
    "/classes/com.korail.mobile.tk.pbpAcepSpec.do": (),
    "/classes/com.korail.mobile.tk.plfNo.do": (),
    "/classes/com.korail.mobile.tk.rcntDlvHst.do": (
        ("Device", "Version", "Key", "custMgNo"),
    ),
}


_COMMUTER_INFO_PATH = "/classes/com.korail.mobile.research.cmtrInfo.do"
_PBP_ACCEPTANCE_PATH = "/classes/com.korail.mobile.tk.pbpAcepSpec.do"
_PLATFORM_NUMBER_PATH = "/classes/com.korail.mobile.tk.plfNo.do"
_REPEATED_TICKET_REFERENCE_PATHS = frozenset(
    {_PBP_ACCEPTANCE_PATH, _PLATFORM_NUMBER_PATH}
)


def _is_commuter_passenger_field_order(
    names: tuple[str, ...],
    scalar_pairs: tuple[tuple[str, str | int], ...],
) -> bool:
    prefix = (
        "Device",
        "Version",
        "Key",
        "jobDvCd",
        "cmtrKndCd",
        "psgCnt",
    )
    if names[: len(prefix)] != prefix:
        return False
    remainder = names[len(prefix) :]
    if not remainder or len(remainder) % 2:
        return False
    count = len(remainder) // 2
    if remainder != (
        *(("cmtrUtlAgeCd",) * count),
        *(("psgPrnb",) * count),
    ):
        return False
    values = dict(scalar_pairs[: len(prefix)])
    return values.get("jobDvCd") == "b" and values.get("psgCnt") == str(count)


def _is_ticket_reference_field_order(
    route_path: str,
    names: tuple[str, ...],
    scalar_pairs: tuple[tuple[str, Any], ...],
) -> bool:
    prefix = ("Device", "Version", "Key", "tkCnt")
    if names[: len(prefix)] != prefix:
        return False
    remainder = names[len(prefix) :]
    if not remainder or remainder != (("tkRetNo",) * len(remainder)):
        return False
    count = scalar_pairs[len(prefix) - 1][1]
    if route_path == _PBP_ACCEPTANCE_PATH:
        if type(count) is not int:
            return False
    elif route_path == _PLATFORM_NUMBER_PATH:
        if (
            not isinstance(count, str)
            or not count
            or any(character < "0" or character > "9" for character in count)
            or str(int(count)) != count
        ):
            return False
        count = int(count)
    else:
        return False
    return count == len(remainder) and all(
        isinstance(value, str) and bool(value)
        for _, value in scalar_pairs[len(prefix) :]
    )


def assert_korail_origin(base_url: str) -> None:
    parsed = urlsplit(base_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise KorailProtocolError(
            "KORAIL request origin is not allowed"
        ) from exc
    if (
        parsed.scheme.casefold() != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() != KORAIL_HTTPS_HOST
        or port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise KorailProtocolError("KORAIL request origin is not allowed")


def assert_read_only_route(method: str, path: str) -> None:
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise KorailProtocolError(
            "KORAIL request target is not a registered relative path: "
            f"{parsed.path}"
        )
    route = (method.upper(), parsed.path)
    if route not in KORAIL_READ_ONLY_ROUTES:
        raise KorailProtocolError(
            f"KORAIL request route is not allowed: {route[0]} {route[1]}"
        )


def assert_mutation_route(method: str, path: str) -> None:
    """Allow only the four evidenced state-changing routes.

    This is the mutation counterpart to :func:`assert_read_only_route`, used
    solely by the dedicated mutation send path. A route must be an exact member
    of :data:`KORAIL_MUTATION_ROUTES`; anything else — including a read-only
    route — is rejected, so the mutation send path can never be repurposed to
    reach an arbitrary or read endpoint.
    """
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise KorailProtocolError(
            "KORAIL request target is not a registered relative path: "
            f"{parsed.path}"
        )
    route = (method.upper(), parsed.path)
    if route not in KORAIL_MUTATION_ROUTES:
        raise KorailProtocolError(
            f"KORAIL mutation route is not allowed: {route[0]} {route[1]}"
        )


def assert_read_only_request_fields(
    path: str,
    values: Mapping[str, Any] | Sequence[tuple[str, Any]],
) -> None:
    route_path = urlsplit(path).path
    if isinstance(values, Mapping):
        scalar_pairs = tuple(values.items())
    elif isinstance(values, Sequence) and not isinstance(
        values,
        (str, bytes, bytearray),
    ):
        scalar_pairs = tuple(values)
        if any(
            type(pair) is not tuple
            or len(pair) != 2
            or not isinstance(pair[0], str)
            for pair in scalar_pairs
        ):
            raise KorailProtocolError(
                "KORAIL ordered request fields must be scalar name/value pairs"
            )
        if route_path not in KORAIL_EXACT_REQUEST_FIELD_ORDERS:
            raise KorailProtocolError(
                "KORAIL ordered request fields are not registered for this route"
            )
    else:
        raise KorailProtocolError(
            "KORAIL request fields must be a mapping or ordered pair sequence"
        )
    allowed = KORAIL_EXACT_REQUEST_FIELDS.get(route_path)
    if allowed is None:
        return
    field_names = [name for name, _ in scalar_pairs]
    has_duplicates = len(field_names) != len(set(field_names))
    if has_duplicates and route_path not in {
        _COMMUTER_INFO_PATH,
        *_REPEATED_TICKET_REFERENCE_PATHS,
    }:
        raise KorailProtocolError(
            "KORAIL request fields must not contain duplicate names"
        )
    ordered_variants = KORAIL_EXACT_REQUEST_FIELD_ORDERS.get(
        route_path
    )
    if ordered_variants is not None:
        names = tuple(field_names)
        valid_shape = names in ordered_variants or (
            route_path == _COMMUTER_INFO_PATH
            and _is_commuter_passenger_field_order(names, scalar_pairs)
        ) or (
            route_path in _REPEATED_TICKET_REFERENCE_PATHS
            and _is_ticket_reference_field_order(
                route_path,
                names,
                scalar_pairs,
            )
        )
    else:
        # Every field must belong to the exact set, and every non-optional
        # field must be present. Optional fields (Retrofit null-omitted @Fields)
        # may be absent, but nothing outside `allowed` is ever accepted.
        optional = KORAIL_OPTIONAL_REQUEST_FIELDS.get(
            route_path, frozenset()
        )
        field_set = set(field_names)
        required = allowed - optional
        valid_shape = required <= field_set <= allowed
    if not valid_shape:
        raise KorailProtocolError(
            "KORAIL request fields must exactly match the registered "
            "read-only contract"
        )
    if any(type(value) not in {str, int} for _, value in scalar_pairs):
        raise KorailProtocolError(
            "KORAIL request values must be scalar strings or integers"
        )


def assert_read_only_form_fields(path: str, fields: set[str]) -> None:
    assert_read_only_request_fields(path, {field: "" for field in fields})

SAFETY_DEFAULTS = {
    "조회성 API": "실제 호출 허용 가능. 단, 계정/티켓 개인정보 로그 마스킹",
    "예약 생성/취소/변경": "기본 비활성화. 명시적 opt-in과 dry-run marker 필요",
    "결제/포인트/현금영수증 발급": "기본 비활성화. 테스트 카드라도 운영 PG endpoint 직접 호출 금지",
    "환불/반환/체크인/회원탈퇴": "기본 비활성화. 별도 confirmation token 필요",
    "PNR/발권번호/N카드 기반 API": "실제 값 없으면 schema-only 테스트만 수행",
}
