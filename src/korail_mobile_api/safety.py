from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from .constants import KORAIL_BASE_URL
from .errors import KorailProtocolError


EXCLUDED_API_DOMAINS = frozenset(
    {
        "reservation",
        "payment",
        "refund",
        "check-in",
        "member-drop",
        "push-sms",
        "points-mileage",
        "dynapath-token-generation",
    }
)

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
    }
)

# Documentation-level tiering of the state-changing routes. These are the four
# core mutation endpoints (one per category). They are deliberately kept OUT of
# KORAIL_READ_ONLY_ROUTES so the read-only allowlist and its guarantee remain
# fully intact: no code path treats a route in this set as callable. This is a
# classification only — the library still has no method that can send any of
# these requests. Each tuple is (HTTP method, exact relative path); the trailing
# comment names the consent category the future mutation method will gate on.
KORAIL_MUTATION_ROUTES = frozenset(
    {
        # reserve
        ("POST", "/classes/com.korail.mobile.certification.TicketReservation"),
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

KORAIL_HTTPS_HOST = urlsplit(KORAIL_BASE_URL).hostname

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
