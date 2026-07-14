from __future__ import annotations

import time

from .config import KorailConfig


def _positive_int(value: int, name: str) -> str:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return str(value)


def _required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _ascii_date(value: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 8
        or any(ch < "0" or ch > "9" for ch in value)
    ):
        raise ValueError(f"{name} must use ASCII YYYYMMDD")
    return value


def _optional_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def build_service_status_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    if timestamp_ms is not None and (
        type(timestamp_ms) is not int or timestamp_ms < 0
    ):
        raise ValueError(
            "timestamp_ms must be a non-negative integer or None"
        )
    resolved = (
        int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    )
    return {"timeStamp": str(resolved)}


def build_cart_list_form(
    pnr_no: str = "",
    additional_service_request_no: str = "",
) -> dict[str, str]:
    return {
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
        "addSrvReqNo": _optional_text(
            additional_service_request_no,
            "additional_service_request_no",
        ),
    }


def build_delay_discount_ticket_form(
    departure_date_to: str,
) -> dict[str, str]:
    return {"dptDtTo": _ascii_date(departure_date_to, "departure_date_to")}


def build_discount_coupon_form(
    page_no: int = 1,
    pnr_no: str = "",
) -> dict[str, str]:
    return {
        "txtSelPage": _positive_int(page_no, "page_no"),
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
    }


def build_pass_availability_form(
    kind_code: str,
    period_code: str,
    age_code: str,
) -> dict[str, str]:
    return {
        "txtCmtrKndCd": _required_text(kind_code, "kind_code"),
        "txtCmtrUtlTrmCd": _required_text(period_code, "period_code"),
        "txtCmtrUtlAgeCd": _required_text(age_code, "age_code"),
    }


def build_trip_menu_form(config: KorailConfig) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
    }


def build_product_reservations_query(
    page_no: int = 1,
    page_size: int = 20,
) -> dict[str, str]:
    return {
        "txtSelPage": _positive_int(page_no, "page_no"),
        "txtCntPerPage": _positive_int(page_size, "page_size"),
    }


def build_product_detail_query(
    reservation_no: str,
    reservation_sequence: str,
) -> dict[str, str]:
    return {
        "txtVrRsNo": _required_text(reservation_no, "reservation_no"),
        "txtVrRsvSqNo": _required_text(
            reservation_sequence,
            "reservation_sequence",
        ),
    }


def build_ticket_receipt_form(
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
) -> dict[str, str]:
    return {
        "h_orgtk_sale_dt": _ascii_date(sale_date, "sale_date"),
        "h_orgtk_wct_no": _required_text(window_no, "window_no"),
        "h_orgtk_sale_sqno": _required_text(
            sale_sequence,
            "sale_sequence",
        ),
        "h_orgtk_tk_ret_pwd": _required_text(
            return_password,
            "return_password",
        ),
    }
