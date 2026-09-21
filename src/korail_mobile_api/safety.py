# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""전선에 나가는 것을 제한하는 가드.

이 모듈에는 실행 로직이 없습니다. 목록과 단언뿐입니다. 어떤 origin·라우트·필드 집합이
허용되는지를 여기 한곳에 모아 두고, :mod:`korail_mobile_api.http` 의 전송 경로가 보내기
직전에 이 단언들을 통과합니다.

가드는 세 갈래입니다.

* **읽기 경로** — :func:`assert_read_only_route` 가 라우트를
  :data:`KORAIL_READ_ONLY_ROUTES` 의 정확한 원소로 제한합니다. 필드 이름·순서 계약은 이
  모듈이 강제하지 않습니다 — 그것을 골든으로 고정하던 테스트가 삭제된 뒤로는 각
  빌더의 코드만이 그 계약을 말합니다.
* **변경 경로** — :func:`assert_mutation_route`,
  :func:`assert_mutation_route_category`, :func:`assert_mutation_form_shape`.
  읽기 라우트를 포함해 :data:`KORAIL_MUTATION_ROUTES` 밖은 전부 거부합니다. 상태를
  바꾸는 메서드 열넷 전부가 이 셋을 지나갑니다 — 하나만 건너뛰던 별도 게이트웨이는
  없어졌습니다.
* **origin** — :func:`assert_korail_origin` 이 API 호스트를 고정합니다.

**대기열 호스트는 여기 없습니다.** ``nf.letskorail.com`` 과 그 노드 풀의 규칙은
:mod:`korail_mobile_api.netfunnel_safety` 에 있습니다. 성격은 같고 파일만 다릅니다 —
두 호스트는 서로에게 닿을 수 없으므로, 메인 API 의 경계를 읽는 사람이 대기열 노드
리다이렉션까지 읽을 이유가 없습니다.

목록의 원소는 전부 APK 의 Retrofit 선언에서 나왔습니다. 근거 없는 라우트나 필드는 여기
없고, 없으면 보낼 수 없습니다.
"""
from collections.abc import Mapping
from typing import Any, Literal
from urllib.parse import urlsplit

from .constants import (
    KORAIL_BASE_URL,
)
from .errors import KorailProtocolError


# WHICH SUBJECT AREAS WERE CONSIDERED AND DECLINED. A record, not a guard --
# the boundary this module actually enforces is KORAIL_READ_ONLY_ROUTES and
# KORAIL_MUTATION_ROUTES below, and nothing else. A frozenset named
# EXCLUDED_API_DOMAINS used to sit here restating it in coarser terms; no
# assert ever read it, so it said "guard" while doing nothing, and it is gone.
#
# Declined: reservation, payment, refund (they have their own mutation routes),
# check-in, member-drop, push-sms, dynapath-token-generation, and the
# password-bearing half of points/mileage. That last one excludes writes and
# auths only, not balance reads:
#   mlg.lpotAthn.do     -- password auth → pwdErrTno (failure counter = state change)
#   xPoint.XPointView   -- same (xpoint_no + xpoint_pwd)
#   xPoint.OkCashbagCertView, mileage.acpnMlgSave.do, mileage.acpnMlgNoti.do
#                       -- registration/accrual writes

# Exact (method, path) pairs the read-only send path will transmit to.
# 58 entries: 56 reads + login and logout POST. Nothing pins the count any
# more -- the suite that did was deleted.
#
# NOTE on certification.ReservationList: two Retrofit overloads share the path.
# Only the read overload (inquiryTicketRsv, CertificationService.java:45-46,
# four query fields) is here; the write overload (applyDisabilityCertification,
# :22) is excluded. The four-field set itself is enforced by http.post_form's
# one targeted exception for this path, not by this route table.
KORAIL_READ_ONLY_ROUTES = frozenset(
    {
        ("POST", "/file/CACHE/MobileService.cache"),
        ("POST", "/file/CACHE/prdMobilePlusMain.cache"),
        ("POST", "/classes/com.korail.mobile.common.code.do"),
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("POST", "/classes/com.korail.mobile.login.Logout"),
        ("POST", "/classes/com.korail.mobile.common.stationinfo"),
        ("POST", "/classes/com.korail.mobile.common.stationdata"),
        ("POST", "/classes/com.korail.mobile.schedule.runDt"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleView"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"),
        (
            "POST",
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
        ),
        ("POST", "/classes/com.korail.mobile.qry.chtnStn.do"),
        ("POST", "/classes/com.korail.mobile.myTicket.MyTicketNewList.do"),
        ("POST", "/ebizcross/getUUID.do"),
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
        ("POST", "/classes/com.korail.mobile.push.crwCallRq.do"),
        ("GET", "/classes/com.korail.mobile.push.cmtrKnd.do"),
        ("GET", "/classes/com.korail.mobile.product.ReservationList"),
        ("GET", "/classes/com.korail.mobile.product.ReservationDetail"),
        ("POST", "/classes/com.korail.mobile.receipt.ReceiptInfo"),
        (
            "POST",
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
        ("POST", "/classes/com.korail.mobile.cust.mchdDcntTgt.do"),
        ("POST", "/classes/com.korail.mobile.research.custTripInfo.do"),
        ("POST", "/classes/com.korail.mobile.copt.gdReqQry.do"),
        ("GET", "/classes/com.korail.mobile.reservation.tripChgDate.do"),
        ("POST", "/classes/com.korail.mobile.research.cmtrInfo.do"),
        ("POST", "/classes/com.korail.mobile.trn.prcFare.do"),
        ("POST", "/classes/com.korail.mobile.tk.dlvRcvCust.do"),
        (
            "POST",
            "/classes/com.korail.mobile.ticket.ticketDupCheck.do",
        ),
        ("POST", "/classes/com.korail.mobile.tk.pbpAcepSpec.do"),
        ("POST", "/classes/com.korail.mobile.tk.rcntDlvHst.do"),
        (
            "POST",
            "/classes/com.korail.mobile.certification.ReservationList",
        ),
        ("POST", "/classes/com.korail.mobile.refunds.CommissionView"),
        ("POST", "/classes/com.korail.mobile.refunds.SelTicketInfo"),
        # 7.0.6 NetworkApi.verifyOnlineRefunds. Verifies a station-issued ticket
        # before the online refund execute route below; it changes nothing itself.
        # Its response does not extend CommonOut -- http._NON_COMMON_OUT_READ_PATHS.
        ("POST", "/classes/com.korail.mobile.refunds.verifyOnlineRefunds"),
        # Loyalty READS. Neither carries a password and neither moves a point:
        # MyXPointView is the my-page summary the app fetches on open
        # (MyPageActivity.java:414) with point_dv_cd pinned to "0" by the DAO
        # itself (KorailPointInquiryDao.java:91), and mlg.amtSpec.do is the
        # 적립/사용 history list. The password-bearing loyalty routes
        # (mlg.lpotAthn.do, xPoint.XPointView) are excluded -- see
        # the declined-areas note at the top of this module.
        ("POST", "/classes/com.korail.mobile.xPoint.MyXPointView"),
        ("POST", "/classes/com.korail.mobile.mlg.amtSpec.do"),
        # 할인카드(N카드) reads. Both are POSTs whose only credential is the
        # session cookie, and neither changes anything: one lists the trips a
        # card has already been spent on, the other lists the trains a card
        # may still be spent on. The two dcntCrd* routes that DO change state
        # (research.dcntCrdInfo.do, reservation.dcntCrdExtn.do) are
        # deliberately absent from this set.
        ("POST", "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do"),
        (
            "POST",
            "/classes/com.korail.mobile.research.dcntCrdScheduleView.do",
        ),
        # 승차권 변경(자율 좌석/열차 변경) 조회 chain. All three are reads that
        # precede a change; none of them commits one.
        #
        # self.seatChgInfo.do (TicketService.java:54-56) answers "which
        # stations and which reasons does this train allow a self seat change
        # for", keyed by the train the ticket is already on
        # (TCSOptionsActivity.java:128-140).
        ("POST", "/classes/com.korail.mobile.self.seatChgInfo.do"),
        # research.tripChgOgtk.do (ResearchService.java:61-63) is the 원표
        # (원승차권) lookup the change chain starts from: it takes N 반환번호
        # tuples and returns the original tickets' journeys and seats
        # (OgTkInquiryDao.java:38-53). Its sibling reservation.tripChgDate.do
        # is already registered above. The chain's three MUTATIONS were
        # removed on 2026-07-27 (22ba4cc); these two reads outlived them.
        ("POST", "/classes/com.korail.mobile.research.tripChgOgtk.do"),
        #
        # DELIBERATELY ABSENT: 특실 업그레이드 myTicket.reqUpgradeSeat
        # (MyTicketService.java:23-24). Its RESPONSE mints a lumpStlTgtNo
        # (SpecialRoomUpgradeDao.java:13,19), making it an unpaid purchase
        # creation — same shape as research.dcntCrdInfo.do. Not registered as a
        # mutation either: its paired write (procUpgradeSeat,
        # MyTicketService.java:20-21) is scoped out.
    }
)

# State-changing routes. Deliberately kept OUT of KORAIL_READ_ONLY_ROUTES:
# the read-only send path refuses every route in this set.
#
# All categories have a callable client method and CAN transmit. What bounds
# them is the route: post_mutation_form sends once assert_mutation_route and
# assert_mutation_route_category both pass, checking the caller's declared
# category against the route's registered one immediately before the POST.
#
# Each tuple is (HTTP method, exact relative path).
KORAIL_MUTATION_ROUTES = frozenset(
    {
        # reserve
        ("POST", "/classes/com.korail.mobile.certification.TicketReservation"),
        # reserve -- 예약대기 follow-up. Same category as the hold: it changes
        # no money, releases no seat, only records two options (좌석등급 변경 /
        # SMS 통보) for a PNR the caller just created
        # (ReservationWaitService.java:10-12).
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
        # 7.0.6 NetworkApi.executeOnlineRefunds -- the money-moving half of the
        # station-ticket refund pair. It settles the amount verifyOnlineRefunds
        # (above, in KORAIL_READ_ONLY_ROUTES) already quoted, so it is the same
        # "refund" category as RefundsRequest.
        ("POST", "/classes/com.korail.mobile.refunds.executeOnlineRefunds"),
        ("POST", "/classes/com.korail.mobile.research.dcntCrdInfo.do"),
        ("POST", "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"),
        # price_recalculation -- 보류된 PNR의 할인 재적용 후 운임 재계산
        # (CertificationService.java:35-37 getDiscountPrice). Its own category:
        # it creates and destroys nothing, but it rewrites what the passenger
        # is about to be charged, which is exactly why it must not borrow the
        # "payment" category, which owns the route that settles the quoted
        # amount.
        #
        # The one route in this set whose form carries REPEATED keys. Its last
        # six @Fields are List<String> and Retrofit emits one key per element
        # with the name unchanged -- RequestBuilder.smali:1537-1601 takes the
        # Iterable branch and calls addField(v3, element) in a loop where v3,
        # the field name, is loop-invariant. There is no index suffix and no
        # bracket. The builder therefore returns list values, which httpx
        # encodes identically.
        ("POST", "/classes/com.korail.mobile.certification.PriceReCalculation"),
        # cart -- 장바구니에 승차권(PNR) 담기 (CartService.java:11-13, addCart).
        # A category of its own rather than a reuse of "reserve": the hold
        # this acts on already exists, the route creates and destroys nothing
        # server-side that this package can observe, and it carries no card
        # number. Confirmed against
        # AddCartDao.java:9-24 and CartService.smali / AddCartDao$AddCartRequest.smali:
        # the request is exactly the common three fields plus "hidPnrNo", and
        # the DAO's response type is a bare BaseResponse (CartService.java:13),
        # same shape as the discount_card extension route above.
        ("POST", "/classes/com.korail.mobile.cart.addCartList"),
        # DELIBERATELY ABSENT: PassService purchase family (pass.passReserve /
        # passPayIssue, PassService.java:19-44). Settlement can only be proven
        # by buying a ₩150,000-250,000 season pass this package cannot refund.
        # 정기권 READS are untouched; no chargeable pass route is here.
    }
)

#: 일곱 가지 상태변경 범주.
MutationCategory = Literal[
    "reserve",
    "payment",
    "cancel",
    "refund",
    "discount_card",
    "price_recalculation",
    "cart",
]

# The category each mutation route belongs to. The mutation send path
# cross-checks the caller-supplied category against the route so a category
# declared for one route (e.g. "reserve") can never be used to POST a
# different category's route (e.g. the refund route).
KORAIL_MUTATION_ROUTE_CATEGORIES = {
    "/classes/com.korail.mobile.certification.TicketReservation": "reserve",
    "/classes/com.korail.mobile.reservationWait.ReservationWait": "reserve",
    "/classes/com.korail.mobile.payment.ReservationPayment": "payment",
    "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk": (
        "cancel"
    ),
    "/classes/com.korail.mobile.refunds.RefundsRequest": "refund",
    "/classes/com.korail.mobile.refunds.executeOnlineRefunds": "refund",
    "/classes/com.korail.mobile.research.dcntCrdInfo.do": "discount_card",
    "/classes/com.korail.mobile.reservation.dcntCrdExtn.do": "discount_card",
    "/classes/com.korail.mobile.certification.PriceReCalculation": (
        "price_recalculation"
    ),
    "/classes/com.korail.mobile.cart.addCartList": "cart",
}


def assert_mutation_route_category(path: str, category: str) -> None:
    """``category`` 가 변경 라우트 ``path`` 를 소유한 범주인지 확인합니다.

    알려진 변경 라우트가 아니거나 호출자가 선언한 범주가 그 라우트에 등록된 범주와
    다르면 :class:`KorailProtocolError` 입니다.
    """
    parsed_path = urlsplit(path).path
    expected = KORAIL_MUTATION_ROUTE_CATEGORIES.get(parsed_path)
    if expected is None:
        raise KorailProtocolError(
            f"KORAIL mutation route is not allowed: {parsed_path}"
        )
    if category != expected:
        raise KorailProtocolError(
            f"KORAIL mutation category {category!r} does not match route "
            f"{parsed_path} (expected {expected!r})"
        )


#: ``mutation_payloads._common_fields`` 가 **모든** 변경 폼에 넣는 세 필드.
#: 이것 없이 전송 경계에 닿은 폼은 이 패키지의 빌더가 만든 것이 아닙니다.
KORAIL_MUTATION_COMMON_FIELDS = frozenset({"Device", "Version", "Key"})


def assert_mutation_form_shape(
    path: str,
    values: Mapping[str, Any],
) -> None:
    """변경 폼의 **모양**을 인코딩 전에 검사합니다.

    일부러 정확한 필드 집합이 아니라 모양 계약입니다. 변경 본문은 읽기처럼 고정된 이름
    목록이 아닙니다 — 예약 폼은 승객·좌석 행 수가 변하고, 운임 재계산은 여섯 개의
    ``@Field List<String>`` 을 반복 키로 보냅니다.

    열 라우트 전부에 걸쳐 변하지 않는 것은 둘입니다. 폼이 문자열→문자열(또는
    문자열→문자열 리스트)의 평평한 매핑이라는 것, 그리고 공통 세 필드
    (:data:`KORAIL_MUTATION_COMMON_FIELDS`)를 싣는다는 것입니다.

    그래서 이 함수는 빌더가 만들 수 없고 손으로 만든 dict 만 만들 수 있는 것을 거부합니다 —
    문자열 아닌 이름, 중첩 매핑, ``None``, 자릿수 없이 인코딩될 ``int``, ``"True"`` 로
    인코딩될 ``bool``. 전선에 거의 맞아 보이는 모양으로 도착하는 것들입니다.
    """
    parsed_path = urlsplit(path).path
    for name, value in values.items():
        if not isinstance(name, str) or not name:
            raise KorailProtocolError(
                f"KORAIL mutation form field names must be non-empty strings; "
                f"{parsed_path} carries {name!r}"
            )
        if isinstance(value, str):
            continue
        if isinstance(value, (list, tuple)) and all(
            isinstance(item, str) for item in value
        ):
            # Repeated wire keys: 운임 재계산's six index-paired lists.
            continue
        raise KorailProtocolError(
            f"KORAIL mutation form field {name!r} on {parsed_path} must be a "
            f"string or a list of strings, not {type(value).__name__}. The "
            "form is sent as-is, so a non-string here reaches the wire in "
            "whatever shape str() gives it."
        )
    missing = KORAIL_MUTATION_COMMON_FIELDS - set(values)
    if missing:
        raise KorailProtocolError(
            f"KORAIL mutation form for {parsed_path} is missing the common "
            f"fields {sorted(missing)}; every builder in this package writes "
            "them via _common_fields, so a form without them did not come "
            "from one"
        )


KORAIL_HTTPS_HOST = urlsplit(KORAIL_BASE_URL).hostname
def assert_korail_origin(base_url: str) -> None:
    """API 요청의 origin 을 ``https://smart.letskorail.com``(443)으로 고정합니다.

    https 가 아니거나, 호스트가 다르거나, 443 이 아닌 포트·userinfo·path·query·fragment 가
    붙어 있으면 :class:`KorailProtocolError` 입니다.
    :class:`~korail_mobile_api.http.KorailHttpClient` 가 생성 시점에 부르므로, 다른
    호스트를 가리키는 설정은 소켓이 생기기 전에 막힙니다. 대기열 호스트는 여기서 거부되며
    자기 가드(:func:`assert_korail_netfunnel_origin`)를 씁니다.
    """
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


def _assert_registered_route(
    method: str,
    path: str,
    routes: frozenset[tuple[str, str]],
    kind: str,
) -> None:
    """The skeleton of both route guards; the table and one word differ.

    Each guard passes its own table, looked up when it is called. The two
    tables are never merged: a route is a read or a mutation, and the send
    path that checks it decides which.
    """
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise KorailProtocolError(
            "KORAIL request target is not a registered relative path: "
            f"{parsed.path}"
        )
    route = (method.upper(), parsed.path)
    if route not in routes:
        raise KorailProtocolError(
            f"KORAIL {kind} route is not allowed: {route[0]} {route[1]}"
        )


def assert_read_only_route(method: str, path: str) -> None:
    """읽기 전용 전송 경로가 갈 수 있는 라우트만 허용합니다.

    ``path`` 는 상대 경로여야 합니다 — scheme·netloc·query·fragment 가 붙으면 거부입니다.
    ``(method, path)`` 쌍이 :data:`KORAIL_READ_ONLY_ROUTES` 의 정확한 원소가 아니면
    :class:`KorailProtocolError` 이고, 변경 라우트도 여기 없으므로 읽기 경로로는 상태를
    바꿀 수 없습니다. 변경 쪽 짝은 :func:`assert_mutation_route` 입니다.
    """
    _assert_registered_route(method, path, KORAIL_READ_ONLY_ROUTES, "request")


def assert_mutation_route(method: str, path: str) -> None:
    """근거가 확인된 상태 변경 라우트만 허용합니다.

    :func:`assert_read_only_route` 의 변경 쪽 짝이며 전용 변경 전송 경로만 사용합니다.
    라우트는 :data:`KORAIL_MUTATION_ROUTES` 의 정확한 원소여야 하고 그 밖은 — 읽기 전용
    라우트를 포함해 — 거부됩니다. 변경 전송 경로를 임의 엔드포인트나 읽기 엔드포인트로
    돌려쓸 수 없습니다.
    """
    _assert_registered_route(method, path, KORAIL_MUTATION_ROUTES, "mutation")


