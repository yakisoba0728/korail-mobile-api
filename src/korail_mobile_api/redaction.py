"""미리보기·로그에 남으면 안 되는 값을 가립니다.

:data:`SENSITIVE_KEYS` = 가려야 할 폼/응답 키 집합. 민감 키의 값은 ``[REDACTED]``,
그 밖의 값에서 발견된 카드번호 모양은 ``[REDACTED_CARD]``.

키 매칭: 대소문자 무시 + 꼬리 인덱스 제거(:func:`is_sensitive_key`).
KORAIL 이 한 필드를 행 번호 붙은 여러 키로 쓰기 때문(``custMgNo_1``, ``txtSeatNo1``).
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
        # --- 인증·세션 ---
        "txtMemberNo",
        "txtPwd",
        "password",
        "JSESSIONID",
        "Cookie",
        "Set-Cookie",
        # --- 응답 메시지(서버가 입력을 인용할 수 있으므로) ---
        "h_msg_txt",
        # --- PNR·예약 식별 ---
        "rsvCnt",
        "pnrNo",
        "hidPnrNo",
        "txtPnrNo",
        "txtPrnNo",
        "pnr_no",
        "prnNo",  # 반환 응답 철자(RefundVerifyTicketDao.java:123,151)
        "h_pnr_no",
        "coptEntRsvNo",
        "pbpRsvNo",
        "pbp_reservation_no",
        "strVrRsvNo",
        "txtVrRsNo",
        "txtVrRsvSqNo",
        "h_vr_rsv_no",
        "virtual_reservation_no",
        "reservation_count",
        # --- 결제·정산 식별 ---
        "tkRetPwd",
        "tkRetNo",
        "h_tk_ret_no",
        "ticket_return_no",
        "return_password",
        "saleWctNo",
        "saleDt",
        "saleSqno",
        "saleDd",  # 세 번째 철자(PaymentService.java:12-14)
        "sale_window_no",
        "sale_date",
        "sale_sequence",
        "h_wct_no",
        "hidWctNo",
        "window_no",
        "h_orgtk_sale_dt",
        "h_orgtk_ret_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_ret_pwd",
        "h_orgtk_tk_ret_pwd",
        "h_orgtk_sale_wct_no",
        "original_sale_date",
        "original_window_no",
        "original_sale_sequence",
        "original_return_password",
        "h_lump_stl_tgt_no",
        "lump_sum_target_no",
        "lumpStlTgtNo",
        "lump_settlement_target_no",
        "lump_settlement_target_nos",
        # --- 카드·결제수단(PaymentMethod 맵, CARD_RE 가 못 잡는 변형) ---
        "hidStlCrCrdNo1",
        "hidVanPwd1",
        "hidCrdVlidTrm1",
        "hidAthnVal1",
        "hidAthnDvCd1",
        "hidIsmtMnthNum1",
        "hidCrdInpWayCd1",
        "mbCrdNo",
        "strMbCrdNo",
        "member_card_no",
        "h_stl_mb_crd_no",
        "h_stl_crd_no",
        "card_no",
        "stlCrdNo",
        "prepCrdNo",
        "prepaid_card_no",
        "settlement_card_no",
        "h_acnt_no",
        "account_no",
        "h_apv_no",
        "apvNo",
        "approval_no",
        "h_xpot_no",
        "point_no",
        # --- 고객 식별(회원번호·이름·전화·생년) ---
        "custMgNo",
        "custMgNo_",  # 인덱스 기본(custMgNo_1 등)
        "acepCustMgFlg",
        "acepCustMgNo",
        "acepCustNm",
        "acepCustTeln",
        "acepCustTeln2",
        "h_cust_no",
        "hidCustNo",
        "strCustNo",
        "encryptCustNo",
        "customer_no",
        "acceptance_customer_management_flag",
        "acceptance_customer_management_no",
        "acceptance_customer_name",
        "acceptance_customer_phone",
        "acceptance_customer_phone_2",
        "strCpNo",   # 로그인 응답 전화번호(LoginDao.java:84-107)
        "strCustNm",
        "strBtdt",
        "strEmailAdr",
        "txtCpNo",   # 예약대기 전화번호(ReservationWaitService.java:12)
        "custTeln",  # 비회원 반환 전화번호(s5/h.java:123)
        # --- 할인카드(N카드) ---
        # h_dcnt_crd_no 는 bearer credential(w4/a.java:100-101)
        "dcntCrdNo",
        "h_dcnt_crd_no",
        "discount_card_no",
        *(f"txtCardNo_{i}" for i in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)),
        "txtCardNo",
        # 할인카드 등록(NCardReservationDao.java:16,29,30)
        "apdCustName",
        "apdCustTeln",
        # --- 승객유형명(코드가 아닌 사람이 읽는 라벨) ---
        # 정책: 사람이 읽는 값은 가리고 코드(psg_tp_dv_cd)는 남긴다.
        "psgTpDvNm",
        "psgTpNm",
        "h_psg_tp_nm",
        "h_dcnt_knd_nm",
        "h_subt_dcs_cl_nm",
        "passenger_type_division_name",
        "member_division_name",
        "acceptance_kind_name",
        "mbDvNm",
        "pbpAcepKndNm",
        # --- 좌석·객실·플랫폼 ---
        "psrmClCd",
        "psrmClNm",
        "psrm_cl_cd",
        "psrm_cl_nm",
        "room_class_code",
        "room_class_name",
        "scarNo",
        "scar_no",
        "seatNo",
        "plfNo",
        "car_no",
        "seat_no",
        "platform_no",
        "h_srcar_no",
        "h_seat_no",
        "h_plf_no",
        # 좌석 지정 출력(SeatSearchActivity.java:679-680)
        *(f"txtSrcarNo{i}" for i in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)),
        *(f"txtSeatNo{i}" for i in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)),
        "txtSrcarNo",
        "txtSeatNo",
        # --- 쿠폰·할인증명·임시직렬 ---
        "h_coup_no",
        "h_cpn_no",
        "h_cert_pwd",
        "coupon_no",
        "certificate_password",
        "hidDscpNo",
        "hidFmlyNo",  # 다자녀 가족(a6/C1041A.java:75)
        "hidRsvChgNo",
        "h_rsv_chg_no",
        "reservation_change_no",
        "h_tmp_job_sqno1",
        "h_tmp_job_sqno2",
        "hidTmpJobSqno1",
        "hidTmpJobSqno2",
        "temporary_job_sequence_1",
        "temporary_job_sequence_2",
        "temporary_job_sequence",
        "tmpJobSqno",
        "chgTno",
        # --- DynaPath·부가서비스·기타 ---
        "x-dynapath-m-token",
        "mutMrkVrfCd",
        "verification_code",
        "addSrvDvCd",
        "additional_service_code",
        "addSrvReqNo",
        "partner_reservation_no",
        "jrnyTpCd",
        "journey_type_code",
        "regDt",
        "registered_date",
        "wdrwPsbFlg",
        "withdrawal_possible_flag",
        "url",
        "image",
        "menuUrl",
        "contUrl",
        "contImage",
        # --- 구매자·동반자·좌석그룹 이름 ---
        "h_sgr_nm",
        "h_buy_ps_nm",
        "h_compa_nm",
        "h_compa_brth",
        "h_comp_nm",
        "h_comp_cert_no",
        "h_wct_nm",
        "seat_group_name",
        "buyer_name",
        "companion_name",
        "companion_birth_date",
        "window_name",
        "certificate_no",
        # --- 반환번호 4분할(RefundService.java:33) ---
        # 16자리가 5/4/5/2 로 분할되어 CARD_RE 에 안 걸림
        "retNo1",
        "retNo2",
        "retNo3",
        "retNo4",
        "retNo",
        "return_no_1",
        "return_no_2",
        "return_no_3",
        "return_no_4",
        "return_no",
        "strName",  # 요청자 이름(s5/c.java:71)
        "requester_name",
        "requester_phone",
        # --- 원표 4분할(ROrtg.java:8-11, RefundService.java:17) ---
        "ogtkSaleDt",
        "ogtkSaleDd",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "ogtk_ret_pwd",
        "ogtk_sale_dt",
        "ogtk_sale_sqno",
        "ogtk_sale_wct_no",
        "original_sale_datetime",
        # --- 지연증명 원표(response/research/Cmpn.java:11-14) ---
        "dlayOgtkRetPwd",
        "dlayOgtkSaleDt",
        "dlayOgtkSaleSqno",
        "dlayOgtkWctNo",
        "delay_certificate_return_password",
        "delay_certificate_sale_date",
        "delay_certificate_sale_sequence",
        "delay_certificate_window_no",
        # --- 구매내역 ---
        "h_purchase_history",
        # --- poppMsg(서버 합성 안내, 입력 인용 가능, RefundVerifyTicketDao.java:66) ---
        "poppMsg",
        "popup_message",
        # --- 이중 인덱스 키(outer=journey/passenger, inner=seat/discount row) ---
        # _index_stripped 는 인덱스 하나만 떼므로 이중 인덱스는 열거 필요
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
    """꼬리 인덱스를 뗀 이름. 없으면 ``None``."""
    match = _INDEX_SUFFIX_RE.match(name)
    if match is None:
        return None
    base = match.group("base")
    return base or None


def is_sensitive_key(name: str) -> bool:
    """``name`` 이 민감 값의 이름인지. 대소문자 무시 + 꼬리 인덱스 제거."""
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
    """문자열에서 카드번호·세션·민감 키값을 가립니다."""
    redacted = CARD_RE.sub("[REDACTED_CARD]", value)
    redacted = SENSITIVE_KEY_VALUE_RE.sub(
        _redact_sensitive_key_value,
        redacted,
    )
    return SESSION_RE.sub(r"\1[REDACTED]", redacted)


def redact_url(value: str) -> str:
    """URL 쿼리 파라미터를 키 단위로 가립니다.

    scheme/netloc 없으면 :func:`redact_text` 로 폴백.
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
    """임의의 값을 재귀적으로 가립니다.

    매핑→키마다, 리스트/튜플→원소마다(컨테이너 타입 유지), 데이터클래스→필드별
    dict, 문자열→:func:`redact_url`. 나머지 타입은 그대로.
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
    """매핑의 각 항목을 :func:`redact_value` 로 가립니다."""
    return {
        key: redact_value(value, key=str(key))
        for key, value in data.items()
    }


def redact_payload(
    payload: Mapping[str, object],
) -> dict[str, str | list[str]]:
    """:class:`~korail_mobile_api.consent.MutationPreview` 용 변경 폼 마스킹.

    민감 키는 ``[REDACTED]``, 나머지는 :func:`redact_text`. 리스트 값은 원소별로
    가리고 길이 유지(``CertificationService.java:35-37`` 의 ``List @Field``).
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
