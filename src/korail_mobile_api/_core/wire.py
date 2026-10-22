# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공통 폼의 삽입 순서를 한곳에서 유지합니다."""

from typing import TypeGuard

from ..config import KorailConfig
from ..constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION


def _device_version(config: KorailConfig) -> dict[str, str]:
    """Key 를 싣지 않는 요청용입니다."""
    fields = {"Device": config.device, "Version": config.version}
    if config.app_version is not None:
        fields["AppVersion"] = config.app_version
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _device_version_key(config: KorailConfig) -> dict[str, str]:
    """7.0.8 공통 DTO의 Device·Version·AppVersion·Key·선택 lang 순서입니다."""
    fields = _device_version(config)
    fields.pop("lang", None)
    fields["Key"] = config.key
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _is_ascii_digits(value: object, lengths: frozenset[int] | None = None) -> TypeGuard[str]:
    """value가 (허용된 길이의) 비지 않은 ASCII 숫자 문자열인지 검사합니다. isdigit 만으로는 전각·위첨자 숫자도 받으므로 isascii 를 함께 봅니다.
    거절 예외와 문구는 호출부가 정합니다."""
    return (
        isinstance(value, str)
        and value.isascii()
        and value.isdigit()
        and (lengths is None or len(value) in lengths)
    )


# 열차·공항버스·N카드 예약이 함께 쓰는 TicketReservationIn 합성 생성자의 선언 순서입니다.
_RESERVATION_KEY_ORDER: tuple[str, ...] = (
    *(
        "Device",
        "Version",
        "AppVersion",
        "Key",
        "lang",
        "txtMenuId",
        "txtJobId",
        "txtGdNo",
        "hidFreeFlg",
        "txtStndFlg",
        "txtTotPsgCnt",
    ),
    *("txtSeatAttCd1", "txtSeatAttCd2", "txtSeatAttCd3", "txtSeatAttCd4", "txtSeatAttCd5", "txtSeatAttCd4_1"),
    *("txtJrnyCnt", "txtSrcarCnt", "txtSrcarCnt1"),
    *(
        f"{field}{row}"
        for row in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        for field in ("txtCompaCnt", "txtPsgTpCd", "txtDiscKndCd", "txtCardNo_")
    ),
    *(
        f"{field}{journey}"
        for journey in (1, 2)
        for field in (
            *(
                "txtJrnyTpCd",
                "txtJrnySqno",
                "txtTrnNo",
                "txtTrnClsfCd",
                "txtTrnGpCd",
                "txtRunDt",
                "txtDptDt",
                "txtDptTm",
            ),
            *("txtDptRsStnCd", "txtDptStnConsOrdr", "txtDptStnRunOrdr", "txtArvRsStnCd", "txtArvStnConsOrdr"),
            *("txtArvStnRunOrdr", "txtChgFlg", "txtPsrmClCd"),
        )
    ),
    *(
        f"{prefix}{seat}"
        for prefixes in (("txtSrcarNo", "txtSeatNo"), ("txtSrcarNo1_", "txtSeatNo1_"))
        for seat in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        for prefix in prefixes
    ),
    *("txtMidRsStnCd", "txtMidStnConsOrdr", "txtMidStnRunOrdr"),
)


def _in_reservation_order(form: dict[str, str]) -> dict[str, str]:
    """표에 없는 키는 원래 순서대로 뒤에 둡니다."""
    ordered = {key: form[key] for key in _RESERVATION_KEY_ORDER if key in form}
    ordered.update(form)
    return ordered
