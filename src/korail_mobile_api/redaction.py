"""미리보기·로그에 남으면 안 되는 값을 가린다.

:data:`SENSITIVE_KEYS` 는 가려야 할 폼/응답 키의 집합이고, 나머지 함수는
그 집합을 문자열·URL·매핑·데이터클래스에 적용한다. 민감한 키의 값은
``[REDACTED]``, 그 밖의 값에서 발견된 카드번호 모양은
``[REDACTED_CARD]`` 가 된다.

키 매칭은 대소문자를 무시하고 꼬리 인덱스를 떼어 본다(:func:`is_sensitive_key`).
KORAIL 이 논리적으로 한 필드를 행 번호가 붙은 여러 키로 쓰기 때문이다 —
``custMgNo_1``, ``txtSeatNo1``.

:func:`redact_payload` 는 :class:`~korail_mobile_api.consent.MutationPreview`
가 쓰는 진입점이다.
"""
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
        # The human-readable special-category labels. psgTpDvNm was registered
        # alone, and the 2026-07-27 read-side sweep found four more spellings
        # carrying the SAME VALUE -- "장애 1~3급", "국가유공자", "만 65세이상"
        # -- that were not. That is not the code-vs-name policy this module
        # documents (mask what a human can read, not the codes standing for
        # it); it is that policy implemented in one spelling out of five.
        #
        # psgTpNm / h_psg_tp_nm are the 승객유형명 as the reservation and
        # refund reads return it; h_dcnt_knd_nm is 할인종류명; h_subt_dcs_cl_nm
        # is the 복지할인 구분명 on the point summary. A spelling that is not
        # here is a spelling that leaks the day a route starts sending it.
        "psgTpDvNm",
        "psgTpNm",
        "h_psg_tp_nm",
        "h_dcnt_knd_nm",
        "h_subt_dcs_cl_nm",
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
        # ------------------------------------------------------------------
        # 반환번호(원표) identity. Both route families that first brought these
        # in were REMOVED on 2026-07-27 -- the 비회원 오프라인 반환 pair
        # (e8fa0e3) and the 여행변경 chain (22ba4cc) -- but the spellings stay:
        # research.tripChgOgtk.do survived both removals and takes the same
        # four-part return number as ogtkSale*_N / ogtkRetPwd_N. The values are
        # identical; only the routes that carry them changed.
        # NOTHING here is caught by a regex:
        # CARD_RE needs 13-19 CONSECUTIVE digits and the 16-digit 반환번호
        # arrives split 5/4/5/2 (res/values/integers.xml:29-32), the phone
        # number is 11 digits, and the requester's name is a Korean name. Key
        # matching is the only thing between these values and a preview.
        #
        # retNo1..4 -- the four segments of the printed 반환번호
        #   (RefundService.java:33). Together they ARE the credential that
        #   turns into a refundable ticket, and the server answers them with
        #   the sale window/date/sequence and the return password
        #   (RefundVerifyTicketDao.java:119-122). Enumerated AND given a base:
        #   is_sensitive_key() would catch retNo1 from the base alone via
        #   _index_stripped, but SENSITIVE_KEY_VALUE_RE matches literals with a
        #   trailing (?![\w-]) and so would NOT catch "retNo1=..." in free
        #   text. Both paths have to be covered.
        # strName -- the 요청자 name on the verify form (s5/c.java:71, the
        #   requestorEdit field of offline_return_input_fragment.xml).
        # custTeln -- the 요청자 phone number on the execute form
        #   (s5/h.java:123). A DISTINCT spelling: acepCustTeln is already
        #   listed but _index_stripped("custteln") is None, so this one was not
        #   covered by anything.
        # ogtkSaleDt / ogtkSaleWctNo / ogtkSaleSqno / ogtkRetPwd -- the camel
        #   spellings of the four-part sale identity on the execute form
        #   (RefundService.java:17). The h_orgtk_* spellings are listed above;
        #   these are the same four values.
        "retNo1",
        "retNo2",
        "retNo3",
        "retNo4",
        "retNo",
        "strName",
        "custTeln",
        "ogtkSaleDt",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        # ...and the verify RESPONSE, which is where the credential comes back.
        #
        # prnNo -- a trap. The response spells the PNR P-r-n
        #   (RefundVerifyTicketDao.java:123,151) and the app feeds it straight
        #   into setPnrNo (s5/h.java:118). pnrNo and txtPrnNo were both listed;
        #   the bare response spelling was not.
        # ogtk_* -- the underscore spellings of the same four-part identity
        #   (RefundVerifyTicketDao.java:119-122), including the return password
        #   in the clear.
        # scar_no / psrm_cl_nm -- the underscore spellings of scarNo/psrmClNm
        #   on the response's seat rows (:169-171).
        "prnNo",
        "ogtk_ret_pwd",
        "ogtk_sale_dt",
        "ogtk_sale_sqno",
        "ogtk_sale_wct_no",
        "scar_no",
        "psrm_cl_nm",
        # poppMsg -- server-composed notice text on a screen whose entire input
        # is a name and a 반환번호 (RefundVerifyTicketDao.java:66;
        # s5/c.java:199-208). Registered for the same reason h_msg_txt already
        # is: server text is free to quote back what the caller sent, and there
        # is no way to tell from here whether it does. It costs nothing to
        # redact -- it is a response field, so no request preview loses
        # anything by it.
        "poppMsg",
        "popup_message",
        # ...and the model attribute names this flow parses into. The response
        # rows reuse attribute names already listed above (pnr_no,
        # original_sale_date, original_window_no, original_sale_sequence,
        # original_return_password, car_no, seat_no, room_class_name); these
        # are the ones that are genuinely new.
        #
        # return_no_1..4 / return_no -- the printed 반환번호's segments,
        #   enumerated and based for the same reason retNo1..4 are. The model
        #   that owned them went with the 비회원 routes; the attribute names are
        #   kept registered because the same four-part number still reaches
        #   tripChgOgtk -- and because a spelling that is dropped here is a
        #   spelling that leaks the day something re-introduces it. The 여행변경
        #   forms that also carried it were removed on 2026-07-27 (22ba4cc).
        "return_no_1",
        "return_no_2",
        "return_no_3",
        "return_no_4",
        "return_no",
        "requester_name",
        "requester_phone",
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
        # travels three ways and none was covered:
        #
        #   * as a bare @Field on the 정기권 원표 조회 branch of
        #     research.cmtrInfo.do (ResearchService.java:41-42; this package
        #     has emitted it since build_commuter_info_form was added),
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
        # 일괄결제대상번호, the number a settlement is charged against.
        # lump_sum_target_no / h_lump_stl_tgt_no are already registered under
        # other spellings; these two are the same number as the 할인카드 구매
        # mutation returns it (mutation_parsers.py maps lumpStlTgtNo ->
        # lump_settlement_target_no), and whoever holds one can have a payment
        # applied to it.
        "lumpStlTgtNo",
        "lump_settlement_target_no",
        # ------------------------------------------------------------------
        # 승차권 여행변경 identity. The three 여행변경 routes were removed on
        # 2026-07-27, but these spellings stay registered: each is a value this
        # set already redacts under a different name, and a spelling dropped
        # here is one that leaks if anything reintroduces the family.
        #
        #   tmpJobSqno IS THE PNR. C5/d.java:145 sets it to
        #     reservationResponse.getH_pnr_no() before the re-price call.
        #     h_pnr_no, pnrNo, txtPnrNo, hidTmpJobSqno1/2, h_tmp_job_sqno1/2
        #     and temporary_job_sequence_1/2 are all already listed; the bare
        #     spelling this route uses was not.
        #   chgTno -- 예약변경 차수 (w4/a.java:136 <- h_rsv_chg_no). The same
        #     value as hidRsvChgNo / h_rsv_chg_no / reservation_change_no.
        #   ogtkSaleWctNo / ogtkSaleDd / ogtkSaleSqno / ogtkRetPwd -- the
        #     원표's four-part 반환번호 (ROrtg.java:8-11). Whoever holds all
        #     four can refund or change the ticket. Single-index keys, so the
        #     base catches ogtkRetPwd_1 via _index_stripped().
        #   lumpStlTgtNo -- the 묶음결제 handle a settlement charges and a
        #     rollback cancels. h_lump_stl_tgt_no and lump_sum_target_no are
        #     listed; the outbound spelling was not.
        "tmpJobSqno",
        "chgTno",
        "ogtkSaleWctNo",
        "ogtkSaleDd",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "lumpStlTgtNo",
        # ...and the model attribute names they parse into.
        "lump_settlement_target_nos",
        "temporary_job_sequence",
        # DOUBLY INDEXED KEYS NEED ENUMERATING, because _index_stripped()
        # removes ONE trailing index: "scarNo_1_1" strips to "scarNo_1", which
        # is not in this set even though "scarNo" is. Rather than change what
        # stripping means for every route in the package, the reachable pairs
        # are spelled out -- the outer index is a journey leg (at most
        # KORAIL_MAX_JOURNEY_LEGS) or a passenger, the inner a seat or a
        # discount row (at most KORAIL_MAX_PASSENGERS_PER_RESERVATION).
        #
        #   scarNo_/seatNo_ (RSrcar.java:8-9) -- the physical seat, already
        #     redacted as scarNo/seatNo/h_srcar_no/h_seat_no elsewhere.
        #   roomClsfCd_/seatPsrmClCd_ (RSeat.java:10,13) -- the cabin, already
        #     redacted as psrmClCd/psrm_cl_cd/room_class_code.
        #   dscpNo_ (RDscp.java:13) -- a spendable coupon/certificate number,
        #     the same value as h_cpn_no/coupon_no/hidDscpNo.
        #   dlayOgtkWctNo_/dlayOgtkSaleDd_/dlayOgtkSaleSqno_/dlayOgtkRetPwd_
        #     (RDscp.java:8-11) -- the 지연할인증's own four-part 반환번호.
        *(
            f"{prefix}{outer}_{inner}"
            for prefix in (
                "scarNo_",
                "seatNo_",
                "roomClsfCd_",
                "seatPsrmClCd_",
                "dscpNo_",
                "dlayOgtkWctNo_",
                "dlayOgtkSaleDd_",
                "dlayOgtkSaleSqno_",
                "dlayOgtkRetPwd_",
            )
            for outer in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
            for inner in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        ),
    }
)
_INDEX_SUFFIX_RE = re.compile(r"^(?P<base>.*?)_?(?P<index>\d+)$")


def _index_stripped(name: str) -> str | None:
    """``name`` 에서 꼬리 인덱스를 뗀 이름, 없으면 ``None``.

    KORAIL 은 논리적으로 하나인 필드를 행 번호 붙은 여러 키로 쓴다. 밑줄이
    있기도 하고(``custMgNo_1``) 없기도 하다(``txtSeatNo1``).
    :data:`SENSITIVE_KEYS` 와 정확히 일치시키면 도달 가능한 첨자를 손으로
    전부 적어야 하고, 하나라도 빠뜨리면 그 철자에서 비밀이 그대로 읽힌다.
    """
    match = _INDEX_SUFFIX_RE.match(name)
    if match is None:
        return None
    base = match.group("base")
    return base or None


def is_sensitive_key(name: str) -> bool:
    """``name`` 이 미리보기나 로그에 절대 닿으면 안 되는 값의 이름인지.

    키 자체를 먼저 보고, 아니면 꼬리 인덱스를 뗀 이름으로 다시 본다. 그래서
    ``custMgNo_7`` 도 ``custMgNo`` 만큼 가려진다.
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
    """문자열 하나에서 카드번호·세션·민감 키의 값을 가린다.

    카드번호 모양(13~19자리, 사이의 공백·하이픈 포함)은 ``[REDACTED_CARD]``,
    ``JSESSIONID=…`` 는 값만 ``[REDACTED]``, ``키=값`` 꼴로 문자열 안에 박힌
    민감 키의 값도 ``[REDACTED]`` 가 된다. 구조를 모르는 로그 한 줄에도 쓸 수
    있도록 정규식만으로 동작한다.
    """
    redacted = CARD_RE.sub("[REDACTED_CARD]", value)
    redacted = SENSITIVE_KEY_VALUE_RE.sub(
        _redact_sensitive_key_value,
        redacted,
    )
    return SESSION_RE.sub(r"\1[REDACTED]", redacted)


def redact_url(value: str) -> str:
    """URL 의 쿼리 파라미터를 키 단위로 가린다.

    scheme 과 netloc 이 없으면 URL 이 아니라고 보고 :func:`redact_text` 로
    넘긴다. URL 이면 쿼리를 파싱해 민감한 키의 값은 통째로 ``[REDACTED]``,
    나머지 값은 :func:`redact_text` 를 거친 뒤 다시 조립한다. 빈 값도 보존한다
    (``keep_blank_values``) — 값이 비어 있다는 사실 자체가 요청의 모양이다.
    """
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
    """임의의 값을 재귀적으로 가린다.

    ``key`` 를 주면 그 이름부터 본다. 민감하면 값을 보지 않고 ``[REDACTED]``
    다. 그렇지 않으면 타입에 따라 내려간다 — 매핑은 키마다,
    리스트·튜플은 원소마다(컨테이너 타입을 유지한다), 데이터클래스는 필드 이름을
    키로 삼아 dict 로 바꾼다. 문자열은 :func:`redact_url` 을 거친다. 나머지
    타입은 그대로 둔다.
    """
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
    """매핑의 각 항목을 키 이름과 함께 :func:`redact_value` 로 가린다.

    응답 봉투나 헤더처럼 최상위가 dict 인 것에 쓴다. 폼/페이로드는 리스트 값을
    따로 다루는 :func:`redact_payload` 쪽이다.
    """
    return {
        key: redact_value(value, key=str(key))
        for key, value in data.items()
    }


def redact_payload(
    payload: Mapping[str, object],
) -> dict[str, str | list[str]]:
    """:class:`~korail_mobile_api.consent.MutationPreview` 를 위해 변경 폼을 가린다.

    민감한 키(카드 필드, 개인정보, PNR)는 전부 ``[REDACTED]`` 가 되고, 남은
    값은 :func:`redact_text` 로 카드 마스킹을 한 번 더 거친다. 예상 못 한 키
    아래 있더라도 원본 카드번호가 미리보기에 뜨지 않는다.

    **리스트 값은 원소별로 가리고 길이가 같은 리스트로 남는다.** 여기서는 폼 키
    하나가 정당하게 여러 값을 실을 수 있기 때문이다 —
    ``certification.PriceReCalculation`` 의 여섯 ``List`` ``@Field`` 는 반복
    키로 나간다. ``str()`` 로 뭉치면 전선 형태 대신 파이썬 repr 이 찍히고, 각
    원소가 리스트의 괄호와 따옴표 뒤로 숨어 :func:`redact_text` 를 피한다.
    길이를 남기는 것은 그것이 비밀이 아니기 때문이다 — 옆에 평문으로 함께 가는
    ``txtPsgGridcnt`` 와 같은 값이다.
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
