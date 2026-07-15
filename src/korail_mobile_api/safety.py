from collections.abc import Mapping
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
    }
)

KORAIL_HTTPS_HOST = urlsplit(KORAIL_BASE_URL).hostname

KORAIL_EXACT_REQUEST_FIELDS = {
    "/file/CACHE/MobileService.cache": frozenset({"timeStamp"}),
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
}
KORAIL_EXACT_FORM_FIELDS = KORAIL_EXACT_REQUEST_FIELDS


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
    values: Mapping[str, Any],
) -> None:
    allowed = KORAIL_EXACT_REQUEST_FIELDS.get(urlsplit(path).path)
    if allowed is None:
        return
    field_names = list(values)
    if len(field_names) != len(set(field_names)):
        raise KorailProtocolError(
            "KORAIL request fields must not contain duplicate names"
        )
    if set(field_names) != allowed:
        raise KorailProtocolError(
            "KORAIL request fields must exactly match the registered "
            "read-only contract"
        )
    if any(type(value) not in {str, int} for value in values.values()):
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
