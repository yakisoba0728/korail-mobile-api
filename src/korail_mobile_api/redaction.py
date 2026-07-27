from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION


SENSITIVE_KEYS = frozenset(
    key.casefold()
    for key in {
        "txtMemberNo",
        "txtPwd",
        "password",
        "JSESSIONID",
        "Cookie",
        "Set-Cookie",
        "h_msg_txt",
        "rsvCnt",
        "pnrNo",
        "hidPnrNo",
        "tkRetPwd",
        "saleWctNo",
        "saleDt",
        "saleSqno",
        "custMgNo",
        "acepCustMgFlg",
        "acepCustMgNo",
        "acepCustNm",
        "acepCustTeln",
        "acepCustTeln2",
        "mbCrdNo",
        "pbpRsvNo",
        "jrnyTpCd",
        "mbDvNm",
        "pbpAcepKndNm",
        "regDt",
        "wdrwPsbFlg",
        "psgTpDvNm",
        "psrmClCd",
        "psrmClNm",
        "scarNo",
        "seatNo",
        "plfNo",
        "x-dynapath-m-token",
        "mutMrkVrfCd",
        "verification_code",
        "addSrvDvCd",
        "additional_service_code",
        "tkRetNo",
        "addSrvReqNo",
        "h_orgtk_tk_ret_pwd",
        "partner_reservation_no",
        "pnr_no",
        "lump_sum_target_no",
        "customer_no",
        "virtual_reservation_no",
        "original_sale_date",
        "window_no",
        "temporary_job_sequence_1",
        "temporary_job_sequence_2",
        "reservation_change_no",
        "certificate_password",
        "sale_sequence",
        "return_password",
        "reservation_count",
        "sale_window_no",
        "sale_date",
        "ticket_return_no",
        "acceptance_customer_management_flag",
        "acceptance_customer_management_no",
        "acceptance_customer_name",
        "acceptance_customer_phone",
        "acceptance_customer_phone_2",
        "pbp_reservation_no",
        "journey_type_code",
        "member_division_name",
        "acceptance_kind_name",
        "registered_date",
        "withdrawal_possible_flag",
        "passenger_type_division_name",
        "room_class_code",
        "room_class_name",
        "car_no",
        "seat_no",
        "platform_no",
        "coupon_no",
        "member_card_no",
        "account_no",
        "approval_no",
        "card_no",
        "point_no",
        "url",
        "image",
        "menuUrl",
        "contUrl",
        "contImage",
        "h_stl_mb_crd_no",
        "h_acnt_no",
        "h_apv_no",
        "h_stl_crd_no",
        "h_xpot_no",
        "coptEntRsvNo",
        "h_pnr_no",
        "h_wct_no",
        "h_tmp_job_sqno1",
        "h_tmp_job_sqno2",
        "h_rsv_chg_no",
        "h_cert_pwd",
        "h_coup_no",
        "h_tk_ret_no",
        "h_lump_stl_tgt_no",
        "h_cust_no",
        "h_vr_rsv_no",
        "h_orgtk_ret_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_ret_pwd",
        "h_cpn_no",
        "strVrRsvNo",
        "txtVrRsNo",
        "txtVrRsvSqNo",
        "h_orgtk_sale_dt",
        # Payment card fields (PaymentMethod map). A mutation preview must
        # never expose card data even though these keys are not yet sent by
        # any callable method. CARD_RE only masks bare PANs; these mask the
        # encrypted/keyed/expiry/CVC/installment variants CARD_RE misses.
        "hidStlCrCrdNo1",
        "hidVanPwd1",
        "hidCrdVlidTrm1",
        "hidAthnVal1",
        "hidAthnDvCd1",
        "hidIsmtMnthNum1",
        "hidCrdInpWayCd1",
        # Reservation identity carried on the payment/cancel forms.
        "txtPnrNo",
        "txtPrnNo",
        "hidWctNo",
        "hidTmpJobSqno1",
        "hidTmpJobSqno2",
        # The 예약대기 follow-up's notification number
        # (ReservationWaitService.java:12). A phone number, and the only PII a
        # reserve-category form has ever carried.
        "txtCpNo",
        # The seat-designated hold's OSrcar keys. car_no/seat_no/h_srcar_no/
        # h_seat_no are already redacted above wherever they are READ back;
        # these are the same two values on the way out. The keys are indexed
        # (txtSrcarNo1..N/txtSeatNo1..N, SeatSearchActivity.java:679-680) and
        # SENSITIVE_KEYS is matched exactly, so every index a reservation can
        # reach is listed -- N is bounded by KORAIL_MAX_PASSENGERS_PER_RESERVATION.
        *(
            f"txtSrcarNo{index}"
            for index in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        ),
        *(
            f"txtSeatNo{index}"
            for index in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        ),
        # Original-ticket sale identity carried on the refund form.
        "h_orgtk_sale_wct_no",
        # Reference-derived reads: certification.ReservationList seat rows and
        # refunds.SelTicketInfo ticket rows. The wire names below are the ones
        # these three routes add on top of the sets already listed above.
        "h_srcar_no",
        "h_seat_no",
        "h_sgr_nm",
        "h_buy_ps_nm",
        "h_compa_nm",
        "h_compa_brth",
        "h_comp_nm",
        "h_comp_cert_no",
        "h_wct_nm",
        "h_plf_no",
        "h_purchase_history",
        # ...and the model attribute names they parse into.
        # 할인카드(N카드) identity. h_dcnt_crd_no is a bearer credential in the
        # strongest sense this API has: w4/a.java:100-101 books a discounted
        # seat by sending nothing but that number and the discount code "153",
        # so anyone holding it can spend someone else's card. dcntCrdNo is the
        # same value on the way out (ResearchService.java:51-52).
        "dcntCrdNo",
        "h_dcnt_crd_no",
        "discount_card_no",
        # ...and the same number on the way OUT, as the reservation form's
        # OPsg.CARD_NO key (OPsg.java:7,13-15). The prefix carries a trailing
        # underscore that the other OPsg prefixes do not, so the transmitted
        # key is txtCardNo_1. A card row is one passenger, so only index 1 can
        # occur today; the whole reachable range is listed anyway, because
        # SENSITIVE_KEYS is matched exactly and a leak here is a spendable
        # credential in a log.
        *(
            f"txtCardNo_{index}"
            for index in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        ),
        "original_window_no",
        "original_sale_sequence",
        "original_return_password",
        "buyer_name",
        "seat_group_name",
        "companion_name",
        "companion_birth_date",
        "window_name",
        "certificate_no",
        # 운임 재계산 (certification.PriceReCalculation) on the way OUT. Its
        # per-row lists carry values this set already redacts under other
        # spellings, and SENSITIVE_KEYS is matched exactly, so the underscore
        # and hid- spellings have to be listed too or the same secret becomes
        # readable purely because this one route names it differently.
        #
        #   hidDscpNo -- the coupon/certificate number backing the discount:
        #     h_cpn_no for a 쿠폰/국가유공자 row (a6/C1042B.java:99,110,140)
        #     and the four-part 지연증명 return number (:128). h_cpn_no,
        #     h_coup_no and coupon_no are all already listed above; this is the
        #     same number on the way out, and a 국가유공자 certificate number
        #     is spendable by whoever holds it.
        #   hidCustNo -- the non-member number (a6/C1042B.java:292), the same
        #     value as h_cust_no / custMgNo / customer_no above.
        #   hidFmlyNo -- the 다자녀 family member's fmlySqno
        #     (a6/C1041A.java:75). It identifies a specific person on the
        #     account.
        #   psrm_cl_cd -- the underscore spelling of psrmClCd, which together
        #     with room_class_code is already redacted.
        "hidDscpNo",
        "hidCustNo",
        "hidFmlyNo",
        "psrm_cl_cd",
        # The 할인카드 registration form's per-row identity
        # (NCardReservationDao.java:16,29,30 -> apdUsrInfo.put(prefix + i, ...)).
        # These are the OUTBOUND spellings of values this set already redacts as
        # acepCustNm/acepCustTeln/custMgNo. They arrive indexed (custMgNo_1,
        # apdCustName_1, apdCustTeln_1), which is why the bases are listed here
        # and _index_stripped() below is what actually catches them: a real
        # name, a phone number and a customer number travel together in one
        # preview row, and together they re-identify a person outright.
        "apdCustName",
        "apdCustTeln",
        # The refund form's original-sale date under its third spelling. The
        # other three quarters of the return-number tuple (window, sequence,
        # password) are already redacted, so leaving this one readable is the
        # only thing standing between a preview and a reconstructable 반환번호.
        "saleDd",
        # 예약변경 차수 on the payment form (PaymentService.java:12-14). Four of
        # the five identity keys beside it are redacted; this was the gap.
        "hidRsvChgNo",
        # The login response's continuation PII (LoginDao.java:84-107). These
        # are held on KorailSession.raw and serialised into the pending-auth
        # string, and mbCrdNo alone was listed -- so the same value was masked
        # or not purely according to which spelling the server used.
        "strCpNo",
        "strCustNm",
        "strBtdt",
        "strEmailAdr",
        "strMbCrdNo",
        "strCustNo",
        "encryptCustNo",
        # Bases for the index-enumerated keys above. The enumerations are kept
        # so that an exact match still works, but these make the family the
        # matched thing rather than each reachable subscript.
        "txtSrcarNo",
        "txtSeatNo",
        "txtCardNo",
        "custMgNo_",
        # 원표(원승차권) identity, on the way OUT and on the way BACK.
        #
        # ogtkRetPwd is a bearer credential in the same sense h_orgtk_ret_pwd
        # already registered above is: it is one quarter of a 반환번호, and the
        # holder of the tuple can read and act on someone else's ticket. It
        # travels three ways and only the third was ever covered:
        #
        #   * as a bare @Query on the 특실 업그레이드 견적
        #     (MyTicketService.java:23-24 -- so it lands in a URL, which is why
        #     redact_url matters here and not just redact_payload),
        #   * as an INDEXED @FieldMap key on the 원표 lookup -- ogtkRetPwd_1,
        #     ogtkRetPwd_2, ... (ROrtg.java:8-11 + TCBookingActivity.java:
        #     169-175). _index_stripped() below turns those back into the base
        #     name, so registering the base covers every row,
        #   * and as a RESPONSE field, OrgTk.ogtkRetPwd
        #     (response/research/OrgTk.java:16), which is the same secret being
        #     handed back.
        #
        # The other three quarters (ogtkSaleWctNo / ogtkSaleDd / ogtkSaleSqno,
        # plus the response's ogtkSaleDt spelling) are registered for the
        # reason this file already states of saleDd at the top of this block:
        # masking three quarters of a return number and leaving one readable is
        # the only thing standing between a log and a reconstructable 반환번호.
        # Note these are DISTINCT keys from the already-registered saleDd /
        # saleWctNo / saleSqno -- an "ogtk" prefix is not an index, so
        # _index_stripped() cannot fall back to them.
        "ogtkRetPwd",
        "ogtkSaleDd",
        "ogtkSaleDt",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        # The same tuple once more under the 지연증명 spelling carried by each
        # companion row of the 원표 response (response/research/Cmpn.java:
        # 11-14). A 지연증명 원표 return number is spendable as a discount.
        "dlayOgtkRetPwd",
        "dlayOgtkSaleDt",
        "dlayOgtkSaleSqno",
        "dlayOgtkWctNo",
        # The 원표 response's settlement rows (response/research/Stl.java:
        # 5-16). h_stl_crd_no / h_apv_no are already registered above; these
        # are a card number, a prepaid card number and an approval number
        # under the spellings THIS route uses.
        "stlCrdNo",
        "prepCrdNo",
        "apvNo",
        # ...and the model attribute names the parsers below put them under.
        "original_sale_datetime",
        "delay_certificate_return_password",
        "delay_certificate_sale_date",
        "delay_certificate_sale_sequence",
        "delay_certificate_window_no",
        "settlement_card_no",
        "prepaid_card_no",
        "approval_no",
        # 특실 업그레이드 견적's 일괄결제대상번호 (SpecialRoomUpgradeDao.java:
        # 15-21). lump_stl_tgt_no / h_lump_stl_tgt_no are already registered
        # under other spellings; this is the same number, and it is what
        # procUpgradeSeat spends (MyTicketService.java:20-21).
        "lumpStlTgtNo",
        "lump_settlement_target_no",
        # 특실 업그레이드 견적's 객실 구분 code. psrmClCd, psrm_cl_cd,
        # room_class_code and room_class_name are all already registered above;
        # roomClsfCd is the same value under the one spelling this route uses,
        # and leaving it readable is precisely the failure the psrm_cl_cd note
        # above was written about.
        "roomClsfCd",
        "room_classification_code",
    }
)
_INDEX_SUFFIX_RE = re.compile(r"^(?P<base>.*?)_?(?P<index>\d+)$")


def _index_stripped(name: str) -> str | None:
    """Return ``name`` without a trailing wire index, or ``None``.

    Korail spells one logical field as many keys by appending a row number,
    sometimes with an underscore (``custMgNo_1``) and sometimes without
    (``txtSeatNo1``). Matching SENSITIVE_KEYS exactly meant every reachable
    subscript had to be enumerated by hand, and a secret stayed readable
    whenever a spelling was missed -- which is exactly how a real name, a phone
    number and a customer number survived into previews.
    """
    match = _INDEX_SUFFIX_RE.match(name)
    if match is None:
        return None
    base = match.group("base")
    return base or None


def is_sensitive_key(name: str) -> bool:
    """Whether ``name`` names a value that must never reach a preview or log.

    Matches the key itself and, failing that, the key with a trailing wire
    index removed, so ``custMgNo_7`` is as redacted as ``custMgNo``.
    """
    folded = name.casefold()
    if folded in SENSITIVE_KEYS:
        return True
    base = _index_stripped(folded)
    return base is not None and base in SENSITIVE_KEYS
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
SESSION_RE = re.compile(r"(?i)(JSESSIONID=)[^&;\s]+")
SENSITIVE_KEY_VALUE_RE = re.compile(
    r"(?P<prefix>(?<![\w-])(?P<key_quote>[\"']?)(?:"
    + "|".join(
        sorted(
            (re.escape(key) for key in SENSITIVE_KEYS),
            key=len,
            reverse=True,
        )
    )
    + r")(?P=key_quote)(?![\w-])\s*(?:=|:)\s*)"
    + r'(?P<value>"(?:\\.|[^"\\])*(?:"|$)'
    + r"|'(?:\\.|[^'\\])*(?:'|$)"
    + r"|[^\s,]+)",
    re.IGNORECASE,
)


def _redact_sensitive_key_value(match: re.Match[str]) -> str:
    value = match.group("value")
    quote = (
        value[0]
        if len(value) >= 2
        and value[0] in {'"', "'"}
        and value[-1] == value[0]
        else ""
    )
    return f"{match.group('prefix')}{quote}[REDACTED]{quote}"


def redact_text(value: str) -> str:
    redacted = CARD_RE.sub("[REDACTED_CARD]", value)
    redacted = SENSITIVE_KEY_VALUE_RE.sub(
        _redact_sensitive_key_value,
        redacted,
    )
    return SESSION_RE.sub(r"\1[REDACTED]", redacted)


def redact_url(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        return redact_text(value)
    query = [
        (
            key,
            "[REDACTED]" if is_sensitive_key(key) else redact_text(item),
        )
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )


def redact_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            item_key: redact_value(item, key=str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: redact_value(getattr(value, field.name), key=field.name)
            for field in fields(value)
        }
    if isinstance(value, str):
        return redact_url(value)
    return value


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: redact_value(value, key=str(key))
        for key, value in data.items()
    }


def redact_payload(
    payload: Mapping[str, object],
) -> dict[str, str | list[str]]:
    """Redact a mutation form/payload mapping for a ``MutationPreview``.

    Every sensitive key (card fields, PII, PNR) becomes ``[REDACTED]``; every
    remaining value is card-masked via :func:`redact_text` so a raw PAN can
    never surface in a preview even when it appears under an unexpected key.

    A LIST value is redacted element by element and stays a list of the same
    length, because one form key here can legitimately carry many values: the
    six ``List`` ``@Field``s of ``certification.PriceReCalculation`` go out as
    repeated keys. Collapsing such a value with ``str()`` would print a Python
    repr in place of the wire form, and — far worse — would hide each element
    from :func:`redact_text` behind the list's own brackets and quotes. The
    length is preserved because it is not a secret: it equals
    ``txtPsgGridcnt``, which travels in the clear beside it.
    """
    redacted: dict[str, str | list[str]] = {}
    for key, value in payload.items():
        name = str(key)
        sensitive = is_sensitive_key(name)
        if isinstance(value, (list, tuple)):
            redacted[name] = [
                "[REDACTED]" if sensitive else redact_text(str(item))
                for item in value
            ]
        else:
            redacted[name] = (
                "[REDACTED]" if sensitive else redact_text(str(value))
            )
    return redacted
